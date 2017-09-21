import sys
import time
import pandas as pd

from ..connection import Connection
from ..connection.rdb import RDBConnection
from ..utils.log import logger
from ..utils.timeutils import datetime_str_to_timestamp, timestamp_to_datetime


class Task(object):
    """
    The task object executed by the parade engine
    """

    DEFAULT_CHECKPOINT = '1970-01-01 00:00:00'
    RET_CODE_SUCCESS = 0
    RET_CODE_FAIL = 1

    def __init__(self):
        """
        _result: the cached task result after execution
        _attributes: the attribute of the task
        :return:
        """
        self._result = None
        self._attributes = {}
        self._result_code = self.RET_CODE_SUCCESS
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
        """
        a string-array to specified the dependant tasks has to be completed before this one
        :return:
        """
        return set()

    @property
    def attributes(self):
        """
        the attributes to transferred to the task result
        :return:
        """
        return self._attributes

    @property
    def result(self):
        """
        the task result
        :return:
        """
        return self._result

    @property
    def result_code(self):
        """
        the task result code
        :return:
        """
        return self._result_code

    def set_attribute(self, key, val):
        self._attributes[key] = val

    @property
    def notify_success(self):
        return False

    @property
    def notify_fail(self):
        return True

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

    def _start(self, context, checkpoint_conn, **kwargs):
        """
        start a checkpoint transaction before executing the task
        :param context:
        :return:
        """
        if not checkpoint_conn:
            return None

        checkpoint_conn.init_record_if_absent()

        assert isinstance(checkpoint_conn, RDBConnection)
        last_record = checkpoint_conn.last_record(self.name)
        if last_record:
            self._last_checkpoint = last_record['checkpoint'].strftime('%Y-%m-%d %H:%M:%S')

        # 基于当前时间,进行粒度对齐后计算本次执行的checkpoint
        now_ts = int(time.time())
        init_ts = datetime_str_to_timestamp(self.DEFAULT_CHECKPOINT, tz=self.checkpoint_timezone)
        checkpoint_ts = now_ts - (now_ts - init_ts) % self.checkpoint_round
        self._checkpoint = timestamp_to_datetime(checkpoint_ts).strftime('%Y-%m-%d %H:%M:%S')

        force = kwargs.get('force', False)

        if self._checkpoint > self._last_checkpoint or force:
            return checkpoint_conn.create_record(self.name, self._checkpoint)
        # 重复执行就直接跳过
        logger.warn('last checkpoint {} indicates the task {} is already executed, bypass the execution'.format(
            self._last_checkpoint, self.name))
        return None

    def _commit(self, context, checkpoint_conn, txn_id):
        """
        commit the checkpoint transaction if the execution succeeds
        :param context:
        :param txn_id:
        :return:
        """
        if not checkpoint_conn:
            return
        checkpoint_conn.commit_record(txn_id)

    def _rollback(self, context, checkpoint_conn, txn_id, err):
        """
        rollback the checkpoint transaction if execution failed
        :param context:
        :param txn_id:
        :param err:
        :return:
        """
        if not checkpoint_conn:
            return
        checkpoint_conn.rollback_record(txn_id, err)

    def execute(self, context, **kwargs):
        """
        the execution process of the etl task
        :param context:
        :param kwargs:
        :return:
        """

        txn_id = None
        checkpoint_conn = context.get_checkpoint_connection()

        if checkpoint_conn is not None:
            txn_id = self._start(context, checkpoint_conn, **kwargs)

        try:
            # run if
            # 1. task record is inited. or
            # 2. checkpoint connection is not specified
            if txn_id or not checkpoint_conn:
                self._result = self.execute_internal(context, **kwargs)
                self.on_commit(context, exec_id=txn_id)

            self._result_code = self.RET_CODE_SUCCESS

            if checkpoint_conn and txn_id:
                self._commit(context, checkpoint_conn, txn_id)

            if self.notify_success and context.get_notifier() is not None:
                context.get_notifier().notify_success(self.name)

        except Exception as e:
            logger.exception(str(e))
            self.on_rollback(context, exec_id=txn_id)
            self._result_code = self.RET_CODE_FAIL
            if self.notify_fail and context.get_notifier() is not None:
                context.get_notifier().notify_error(self.name, str(e))

            if checkpoint_conn and txn_id:
                self._rollback(context, checkpoint_conn, txn_id, e)

    def on_commit(self, context, **kwargs):
        pass

    def on_rollback(self, context, **kwargs):
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
        raise NotImplementedError("The target is required")

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
    def target_pkey(self):
        """
        a string or a string-tuple to specify the primary key on the target table
        :return:
        """
        return None

    @property
    def target_indexes(self):
        """
        a string or a string-tuple or a string/string-tuple list to specify the indexes on the target table
        :return:
        """
        """
        :return:
        """
        return []

    @property
    def target_checkpoint_column(self):
        """
        the columns to use as the clue of last/checkpoint in target table
        :return:
        """
        return None

    def execute_internal(self, context, **kwargs):
        """
        the internal execution process to be implemented
        :param context:
        :param kwargs:
        :return:
        """
        raise NotImplementedError

    def on_commit(self, context, **kwargs):
        target_df = self._result

        if not sys.stdout.isatty():
            target_df.to_json(sys.stdout, orient='records')
            return

        target_conn = context.get_connection(self.target_conn)

        if self.target_pkey:
            assert isinstance(self.target_pkey, str) or isinstance(self.target_pkey, tuple), \
                "target primary key can only be of type string or tuple"

        if not self.target_indexes:
            indexes = []
        elif isinstance(self.target_indexes, tuple):
            indexes = [self.target_indexes]
        else:
            indexes = self.target_indexes

        for index in indexes:
            assert isinstance(index, str) or isinstance(index, tuple), \
                "target indexes can only be of type string or tuple"
        target_conn.store(target_df, self.target_table,
                          if_exists=self.target_mode,
                          chunksize=kwargs.get('chunksize', 10000),
                          typehints=self.target_typehints,
                          checkpoint=self._checkpoint,
                          last_checkpoint=self._last_checkpoint,
                          checkpoint_column=self.target_checkpoint_column,
                          pkey=self.target_pkey,
                          indexes=indexes)


class SingleSourceETLTask(ETLTask):
    @property
    def source_conn(self):
        """
        the source connection to write the result
        :return:
        """
        raise NotImplementedError("The source connection is required")

    @property
    def source(self):
        raise NotImplementedError("The source is required")

    @property
    def is_source_query(self):
        return True

    def transform(self, df):
        return df

    def execute_internal(self, context, **kwargs):
        source_conn = context.get_connection(self.source_conn)
        assert isinstance(source_conn, Connection)
        df = pd.read_json(sys.stdin, orient='records') if not sys.stdin.isatty() else source_conn.load_query(
            self.source) if self.is_source_query else source_conn.load(self.source)
        # df = source_conn.load_query(self.source) if self.is_source_query else source_conn.load(self.source)
        return self.transform(df)


class APITask(Task):
    ATTR_TOTAL_ELEMENTS = 'totalElements'
    ATTR_VIEW_LABELS = 'labels'
    ATTR_EXPORT_LABELS = 'export_labels'

    def execute_internal(self, context, **kwargs):
        raise NotImplementedError

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


class Milestone(Task):
    def __init__(self):
        Task.__init__(self)
        self._deps = []
        self._notify_success = False

    def set_deps(self, deps):
        self._deps = deps

    def enable_notify_success(self):
        self._notify_success = True

    def disable_notify_success(self):
        self._notify_success = False

    def execute_internal(self, context, **kwargs):
        pass

    @property
    def deps(self):
        raise self._deps

    @property
    def notify_success(self):
        return self._notify_success
