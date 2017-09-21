import datetime

import pandas as pd
from sqlalchemy import create_engine, MetaData, Column, types, Index, Table
from sqlalchemy.sql import functions

from parade.utils.log import logger
from . import Connection, Datasource


class RDBConnection(Connection):
    def __init__(self, datasource):
        Connection.__init__(self, datasource)
        assert isinstance(datasource, Datasource), 'Invalid connection provided'
        # assert connection.host is not None, 'host of connection is required'
        # assert connection.port is not None, 'port of connection is required'
        # assert connection.db is not None, 'db of connection is required'
        # assert connection.protocol is not None, 'protocol of connection is required'
        self.metadata = MetaData()
        self.task_table = Table('sys_task_record', self.metadata,
                                Column('id', types.BigInteger, autoincrement=True, primary_key=True),
                                Column('task', types.String(64), nullable=False),
                                Column('checkpoint', types.DateTime, default=datetime.datetime.now),
                                Column('create_time', types.DateTime, default=datetime.datetime.now),
                                Column('commit_time', types.DateTime, default=datetime.datetime.now),
                                Column('update_time', types.DateTime, default=datetime.datetime.now,
                                       onupdate=datetime.datetime.now),
                                Column('status', types.Integer, default=0),
                                Column('message', types.String(256), default='OK'),

                                Index('idx_task_create', 'task', 'create_time'),
                                )

    def open(self):
        uri = self.datasource.uri
        if uri is None:
            authen = None
            uripart = self.datasource.host + ':' + str(self.datasource.port) + '/' + self.datasource.db
            if self.datasource.user is not None:
                authen = self.datasource.user
            if authen is not None and self.datasource.password is not None:
                authen += ':' + self.datasource.password
            if authen is not None:
                uripart = authen + '@' + uripart
            uri = self.datasource.protocol + '://' + uripart
        pandas_conn = create_engine(uri, encoding="utf-8")
        return pandas_conn

    def load(self, table, **kwargs):
        return self.load_query('select * from {}'.format(table))

    def load_query(self, query, **kwargs):
        conn = self.open()
        return pd.read_sql_query(query, con=conn)

    def store(self, df, table, **kwargs):
        assert isinstance(df, pd.DataFrame), "Invalid data type"
        if_exists = kwargs.get('if_exists', 'fail')
        chunksize = kwargs.get('chunksize', 10000)
        pkey = kwargs.get('pkey', None)
        indexes = kwargs.get('indexes', [])
        checkpoint_column = kwargs.get('checkpoint_column', None)
        checkpoint = kwargs.get('checkpoint')
        last_checkpoint = kwargs.get('last_checkpoint')

        _conn = self.open()

        if if_exists == 'append' or if_exists == 'update':
            target_table = Table(table, MetaData(), autoload=True, autoload_with=_conn)
            assert checkpoint_column is not None, "checkpoint_column is required in update mode!"
            assert (isinstance(checkpoint_column, tuple) and len(checkpoint_column) == 2) or isinstance(checkpoint_column, str), "checkpoint_column can only be str or 2-tuple!"

            if isinstance(checkpoint_column, tuple):
                (create_time_column, update_time_column) = checkpoint_column
            else:
                create_time_column = checkpoint_column
                update_time_column = checkpoint_column

            # delete extra records over last checkpoint in append/update mode
            clear_ins = target_table.delete().where(Column(update_time_column) >= last_checkpoint)
            _conn.execute(clear_ins)

            if if_exists == 'update':
                assert pkey is not None, "primary key is required in update mode!"
                assert isinstance(pkey, str), "update mode only support single primary key"
                update_df = df[df[create_time_column] < last_checkpoint]
                if not update_df.empty:
                    logger.info(table + ": find {} records to update".format(len(update_df)))
                    update_keys = list(update_df[pkey])
                    delete_ins = target_table.delete().where(Column(pkey).in_(update_keys))
                    _conn.execute(delete_ins)
                if_exists = 'append'

        schema = None
        if table.find('.') >= 0:
            toks = table.split('.', 1)
            schema = toks[0]
            table = toks[1]

        float_columns = list(df.select_dtypes(include=['float64', 'float']).keys())
        if len(float_columns) > 0:
            logger.warn(table +
                    ": Detect columns with float types {}, you better check if this is caused by NAN-integer column issue of pandas!".format(
                            list(float_columns)))

        typehints = dict()
        obj_columns = list(df.select_dtypes(include=['object']).keys())

        if len(obj_columns) > 0:
            logger.warn(table +
                    ": Detect columns with object types {}, which is automatically converted to *VARCHAR(256)*, you can override this by specifying type hints!".format(
                            list(obj_columns)))
        import sqlalchemy.types as sqltypes
        typehints.update(dict((k, sqltypes.VARCHAR(256)) for k in obj_columns))

        # TODO: upddate typehints with user-specified one
        _typehints = kwargs.get('typehints', {})
        from parade.type import stdtype_to_sqltype
        for col, stdtype in _typehints.items():
            logger.info(table + ": Column [{}] is set to type [{}]".format(col, str(stdtype)))
            typehints[col] = stdtype_to_sqltype(stdtype)

        def _chunks(_df, _chunksize):
            """Yield successive n-sized chunks from l."""
            for i in range(0, len(_df), _chunksize):
                yield df[i:i + _chunksize]

        # still write to database for empty dataframe
        if df.empty:
            df.to_sql(name=table, con=_conn, index=False, schema=schema, if_exists=if_exists, dtype=typehints)
            logger.warn(table + ": Write to {}: empty dataframe".format(table))
        else:
            for idx, chunk in enumerate(_chunks(df, chunksize)):
                if_exists_ = 'append' if idx > 0 else if_exists
                chunk.to_sql(name=table, con=_conn, index=False, schema=schema, if_exists=if_exists_, dtype=typehints)
                logger.info(table + ": Write to {}: rows #{}-#{}".format(table, idx * chunksize, (idx + 1) * chunksize))

        if if_exists == 'replace':
            if pkey:
                pkeys = pkey if isinstance(pkey, str) else ','.join(pkey)
                _conn.execute('ALTER TABLE {} ADD PRIMARY KEY ({})'.format(table, pkeys))

            for index in indexes:
                index_str = index if isinstance(index, str) else ','.join(index)
                index_name = index if isinstance(index, str) else '_'.join(index)
                _conn.execute('ALTER TABLE {} ADD INDEX idx_{} ({})'.format(table, index_name, index_str))

    def init_record_if_absent(self):
        _conn = self.open()
        if not self.task_table.exists(_conn):
            try:
                self.task_table.create(_conn)
            except:
                pass

    def last_record(self, task_name):
        _conn = self.open()
        _query = self.task_table.select(). \
            where(self.task_table.c.task == task_name). \
            where(self.task_table.c.status == 1). \
            order_by(self.task_table.c.create_time.desc()).limit(1)
        _last_record = _conn.execute(_query).fetchone()

        if _last_record is not None:
            return dict(_last_record)
        return None

    def create_record(self, task_name, new_checkpoint):
        _conn = self.open()

        # 创建待提交checkpoint
        ins = self.task_table.insert().values(task=task_name, checkpoint=new_checkpoint)
        return _conn.execute(ins).inserted_primary_key[0]

    def commit_record(self, txn_id):
        _conn = self.open()
        sql = self.task_table.update(). \
            where(self.task_table.c.id == txn_id). \
            values(status=1, commit_time=functions.now())
        _conn.execute(sql)

    def rollback_record(self, txn_id, err):
        _conn = self.open()
        sql = self.task_table.update(). \
            where(self.task_table.c.id == txn_id). \
            values(status=2, message=str(err))
        _conn.execute(sql)
