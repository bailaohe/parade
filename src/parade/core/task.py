import time

from ..connection import Connection
from ..connection.rdb import RDBConnection
from ..utils.log import logger
from ..utils.timeutils import datetime_str_to_timestamp, timestamp_to_datetime


class Task(object):
    """
    The task object executed by the parade engine
    """

    DEFAULT_CHECKPOINT = '1970-01-01 00:00:00'

    def __init__(self):
        """
        _result: the cached task result after execution
        _attributes: the attribute of the task
        :return:
        """
        self._result = None
        self._attributes = {}
        self._last_checkpoint = self.DEFAULT_CHECKPOINT
        self._checkpoint = self.DEFAULT_CHECKPOINT

    @property
    def name(self):
        """
        get the identifier of the task, the default is the class name of task
        :return: the task identifier
        """
        # class_name = self.__class__.__name__
        # task_name = ''
        # for _s_ in class_name:
        #     task_name += _s_ if _s_.islower() else '_' + _s_.lower()
        # return task_name[task_name.startswith("_") and 1:]
        return self.__module__.split('.')[-1]

    @property
    def deps(self):
        return set()

    @property
    def attributes(self):
        """
        the attributes to transferred to the task result
        :return:
        """
        return self._attributes

    def set_attribute(self, key, val):
        self._attributes[key] = val

    @property
    def checkpoint_round(self):
        """
        the time interval the checkpoint will align to
        default value is 1 day
        :return:
        """
        return 3600 * 24

    @property
    def checkpoint_timezone(self):
        """
        the timezone used when recording checkpoint
        default: None, use the local timezone
        :return:
        """
        return None

    @property
    def checkpoint_conn(self):
        """
        the connection to record the checkpoint
        default value is the target connection
        :return:
        """
        return self.target_conn

    # @property
    # def checkpoint_column(self):
    #     """
    #     the column to use as the clue for checkpoint
    #     :return:
    #     """
    #     if self.target_mode == 'append':
    #         raise NotImplementedError
    #     return None

    def _start(self, context):
        """
        start a checkpoint transaction before executing the task
        :param context:
        :return:
        """
        checkpoint_conn = context.get_connection(self.checkpoint_conn)
        assert isinstance(checkpoint_conn, RDBConnection)
        last_record = checkpoint_conn.last_record(self.name)
        if last_record:
            self._last_checkpoint = last_record['checkpoint'].strftime('%Y-%m-%d %H:%M:%S')

        # 基于当前时间,进行粒度对齐后计算本次执行的checkpoint
        now_ts = int(time.time())
        init_ts = datetime_str_to_timestamp(self.DEFAULT_CHECKPOINT, tz=self.checkpoint_timezone)
        checkpoint_ts = now_ts - (now_ts - init_ts) % self.checkpoint_round
        self._checkpoint = timestamp_to_datetime(checkpoint_ts).strftime('%Y-%m-%d %H:%M:%S')

        if self._checkpoint > self._last_checkpoint:
            return checkpoint_conn.create_record(self.name, self._checkpoint)
        # 重复执行就直接跳过
        logger.warn('last checkpoint {} indicates the task is already executed, bypass the execution'.format(
                self._last_checkpoint))
        return None

    def _commit(self, context, txn_id):
        """
        commit the checkpoint transaction if the execution succeeds
        :param context:
        :param txn_id:
        :return:
        """
        checkpoint_conn = context.get_connection(self.checkpoint_conn)
        checkpoint_conn.commit_record(txn_id)

    def _rollback(self, context, txn_id, err):
        """
        rollback the checkpoint transaction if execution failed
        :param context:
        :param txn_id:
        :param err:
        :return:
        """
        checkpoint_conn = context.get_connection(self.checkpoint_conn)
        checkpoint_conn.rollback_record(txn_id, err)

    def execute(self, context, **kwargs):
        """
        the execution process of the etl task
        :param context:
        :param kwargs:
        :return:
        """
        txn_id = self._start(context)
        try:
            if txn_id:
                self._result = self.execute_internal(context, **kwargs)
                self.on_commit(context, txn_id)
                self._commit(context, txn_id)
        except Exception as e:
            logger.exception(str(e))
            self._rollback(context, txn_id, e)
            self.on_rollback(context, txn_id)

    def on_commit(self, context, txn_id, **kwargs):
        pass

    def on_rollback(self, context, txn_id, **kwargs):
        pass

    def execute_internal(self, context, **kwargs):
        """
        the execution process of the task
        :param context: the executor context
        :param kwargs: the task arguments
        :return: the task result
        """
        raise NotImplementedError


class ETLTask(Task):
    @property
    def target_conn(self):
        """
        the target connection to write the result
        :return:
        """
        raise NotImplemented("The target is required")

    @property
    def target_table(self):
        """
        the target table to store the result
        :return:
        """
        return self.name

    @property
    def target_mode(self):
        """
        what to do if the target table exists, replace / append / fail
        :return:
        """
        return 'replace'

    @property
    def target_typehints(self):
        """
        a dict of column_name => datatype, to customize the data type before write target
        :return:
        """
        return {}

    @property
    def target_index(self):
        return None

    def execute_internal(self, context, **kwargs):
        """
        the internal execution process to be implemented
        :param context:
        :param kwargs:
        :return:
        """
        raise NotImplemented

    def on_commit(self, context, txn_id, **kwargs):
        target_df = self._result
        if self.target_index:
            target_df.set_index(self.target_index)
        target_conn = context.get_connection(self.target_conn)
        target_conn.store(target_df, self.target_table,
                          if_exists=self.target_mode,
                          chunksize=kwargs.get('chunksize', 10000),
                          typehints=self.target_typehints)


class SqlETLTask(ETLTask):
    @property
    def source_conn(self):
        """
        the source connection to write the result
        :return:
        """
        raise NotImplemented("The source is required")

    @property
    def etl_sql(self):
        """
        the single sql statement to process etl
        :return:
        """
        raise NotImplemented("The etl-sql is required")

    def execute_internal(self, context, **kwargs):
        source_conn = context.get_connection(self.source_conn)
        assert isinstance(source_conn, Connection)
        df = source_conn.load_query(self.etl_sql)
        return df


class APITask(Task):
    ATTR_TOTAL_ELEMENTS = 'totalElements'
    ATTR_VIEW_LABELS = 'labels'
    ATTR_EXPORT_LABELS = 'export_labels'

    def execute_internal(self, context, **kwargs):
        raise NotImplemented

    def execute(self, context, **kwargs):
        raw = self.execute_internal(context, **kwargs)
        self._attributes[APITask.ATTR_VIEW_LABELS] = self.labels
        self._attributes[APITask.ATTR_EXPORT_LABELS] = self.export_labels
        return raw

    @property
    def labels(self):
        return {}

    @property
    def export_labels(self):
        return {}
