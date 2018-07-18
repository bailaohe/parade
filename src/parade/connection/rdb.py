import pandas as pd
from ..core import Plugin
from sqlalchemy import create_engine, MetaData, Column, Table
from sqlalchemy.exc import NoSuchTableError

from parade.utils.log import parade_logger as logger
from . import Connection


class RDBConnection(Connection):
    def __init__(self):
        Plugin.__init__(self)

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
            uri = self.datasource.protocol + '://' + uripart + '?charset=utf8'
        return create_engine(uri, encoding="utf-8", pool_size=16, pool_recycle=300)

    def load(self, table, **kwargs):
        return self.load_query('select * from {}'.format(table))

    def load_query(self, query, **kwargs):
        conn = self.open()
        df = pd.read_sql_query(query, con=conn)

        logger.info("before memory: " + str(df.memory_usage(deep=True).sum() / 1024**2) + " MB")
        # 优化内存使用
        # 1.使用子类型优化数字列
        df_int = df.select_dtypes(include=['int64'])
        convert_int = df_int.apply(pd.to_numeric, downcast='unsigned')
        for col in df_int.columns:
            df[col] = convert_int[col]

        # 2.使用分类来优化对象类型
        df_obj = df.select_dtypes(include=['object'])
        if len(df_obj.columns)>0:
            for col in df_obj.columns:
                num_unique_values = len(df_obj[col].unique())
                num_total_values = len(df_obj[col])
                if num_total_values > 0 and num_unique_values / num_total_values < 0.5:
                    df[col] = df[col].astype('category')
        logger.info("after memory: " + str(df.memory_usage(deep=True).sum() / 1024 ** 2) + " MB")
        return df

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

        try:
            if if_exists == 'append' or if_exists == 'update':
                target_table = Table(table, MetaData(), autoload=True, autoload_with=_conn)
                assert checkpoint_column is not None, "checkpoint_column is required in update mode!"
                assert (isinstance(checkpoint_column, tuple) and len(checkpoint_column) == 2) or isinstance(
                    checkpoint_column, str), "checkpoint_column can only be str or 2-tuple!"

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
        except NoSuchTableError:
            if_exists = 'replace'

        schema = None
        if table.find('.') >= 0:
            toks = table.split('.', 1)
            schema = toks[0]
            table = toks[1]

        float_columns = list(df.select_dtypes(include=['float64', 'float']).keys())
        if len(float_columns) > 0:
            logger.warn(table +
                        ": Detect columns with float types {}, you better check if this is caused by NAN-integer "
                        "column issue of pandas!".format(
                            list(float_columns)))

        typehints = dict()
        obj_columns = list(df.select_dtypes(include=['object']).keys())

        if len(obj_columns) > 0:
            logger.warn(table +
                        ": Detect columns with object types {}, which is automatically converted to *VARCHAR(256)*, "
                        "you can override this by specifying type hints!".format(
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
