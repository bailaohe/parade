import pandas as pd
from sqlalchemy import create_engine, text

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
        if_exists = kwargs['if_exists'] if 'if_exists' in kwargs else 'fail'
        chunksize = kwargs['chunksize'] if 'chunksize' in kwargs else None
        schema = None
        if table.find('.') >= 0:
            toks = table.split('.', 1)
            schema = toks[0]
            table = toks[1]

        floatcolumns = list(df.select_dtypes(include=['float64', 'float']).keys())
        if len(floatcolumns) > 0:
           logger.warn(
                        "Detect columns with float types {}, you better check if this is caused by NAN-integer column issue of pandas!".format(
                                list(floatcolumns)))

        typehints = dict()
        objcolumns = list(df.select_dtypes(include=['object']).keys())

        if len(objcolumns) > 0:
           logger.warn(
                   "Detect columns with object types {}, which is automatically converted to *VARCHAR(256)*, you can override this by specifying type hints!".format(
                                list(objcolumns)))
        import sqlalchemy.types as sqltypes
        typehints.update(dict((k, sqltypes.VARCHAR(256)) for k in objcolumns))

        # TODO: upddate typehints with user-specified one
        _typehints = kwargs.get('typehints', {})
        from parade.type import stdtype_to_sqltype
        for col, stdtype in _typehints.items():
            logger.info("Column [{}] is set to type [{}]".format(col, str(stdtype)))
            typehints[col] = stdtype_to_sqltype(stdtype)

        def _chunks(_df, _chunksize):
            """Yield successive n-sized chunks from l."""
            for i in range(0, len(_df), _chunksize):
                yield df[i:i + _chunksize]

        for idx, chunk in enumerate(_chunks(df, chunksize)):
            if_exists_ = if_exists
            if idx > 0:
                if_exists_ = 'append'
            chunk.to_sql(name=table, con=self.open(), index=False, schema=schema, if_exists=if_exists_,
                         #chunksize=chunksize,
                         dtype=typehints)
            logger.info("Write rows #{}-#{}".format(idx * chunksize, (idx + 1) * chunksize))

    def last_record(self, task_name):
        _conn = self.open()
        sql = text("""
            SELECT * FROM _task_record
                WHERE task=:task_name AND status=1 ORDER BY create_time desc LIMIT 1
        """)

        _last_record = _conn.execute(sql, task_name=task_name).fetchone()

        if _last_record is not None:
            # return _raw_last_checkpoint[0].strftime("%Y-%m-%d %H:%M:%S")
            return dict(_last_record)
        return None

    def create_record(self, task_name, new_checkpoint):
        _conn = self.open()
        from sqlalchemy import Table
        from sqlalchemy import MetaData
        # TODO append方式下回收超出本次checkpoint的数据
        # if self.get_target_mode() == 'append':
        #     target_table = Table(self.get_target_table(), MetaData(), autoload=True, autoload_with=target_conn)
        #     clear_ins = target_table.delete(whereclause="TIMESTAMP(" + self.checkpoint_column + ") >= '" + self._last_checkpoint + "'")
        #     target_conn.execute(clear_ins)
        # 创建待提交checkpoint
        task_table = Table('_task_record', MetaData(), autoload=True, autoload_with=_conn)
        ins = task_table.insert().values(task=task_name, checkpoint=new_checkpoint)
        return _conn.execute(ins).inserted_primary_key[0]

    def commit_record(self, txn_id):
        _conn = self.open()
        sql = text("""
            UPDATE _task_record SET status = 1, commit_time = now(), update_time = now()
            WHERE id = :id
        """)
        _conn.execute(sql, id=txn_id)

    def rollback_record(self, txn_id, err):
        _conn = self.open()
        sql = text("""
            UPDATE _task_record SET status = 2, message = :err, update_time = now()
            WHERE id = :id
        """)
        _conn.execute(sql, err=str(err), id=txn_id)
