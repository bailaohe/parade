import json
import sys
import time

import pandas as pd

from ..connection import Connection
from ..utils.log import logger
from ..utils.timeutils import datetime_str_to_timestamp, timestamp_to_datetime


class Task(object):
    """
    The task object executed by the parade engine
    """
    RET_CODE_SUCCESS = 0
    RET_CODE_FAIL = 1

    STATE_INIT = (0, 'Created')[0]
    STATE_PENDING = (1, 'Pending')[0]
    STATE_EXECUTING = (2, 'Executing')[0]
    STATE_SUCCESS = (3, 'Succeeded')[0]
    STATE_FAILED = (4, 'Failed')[0]
    STATE_CANCELLED = (5, 'Cancelled')[0]

    def __init__(self):
        """
        _result: the cached task result after execution
        _attributes: the attribute of the task
        :return:
        """
        self._result = None
        self._attributes = {}
        self._result_code = self.RET_CODE_SUCCESS
        self.exec_id = 0
        self._state = self.STATE_INIT
        self.flow_id = 0
        self._flow = None

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
        """
        set the task attribute
        :param key:
        :param val:
        :return:
        """
        self._attributes[key] = val

    @property
    def notify_success(self):
        return False

    @property
    def notify_fail(self):
        return True

    def on_start(self, context, **kwargs):
        """
        start a checkpoint transaction before executing the task
        :param context:
        :return:
        """

        assert self._state == self.STATE_PENDING
        return self.STATE_EXECUTING

    def pending(self, context, flow_id=0, flow=None):
        """
        Initialize the task to *pending* state
        :return:
        """
        self.flow_id = flow_id
        self._flow = flow

        self._state = self.STATE_PENDING
        self.on_pending(context)
        self.exec_id = context.on_task_pending(self.name, self.attributes, flow_id, flow)

    def on_pending(self, context):
        pass

    def cancel(self, context, fail_deps):
        self._state = self.STATE_CANCELLED
        self.on_cancel(context)
        context.on_task_cancelled(self, fail_deps)

    def on_cancel(self, context):
        pass

    def execute(self, context, **kwargs):
        """
        the execution process of the etl task
        :param context:
        :param kwargs:
        :return:
        """

        new_state = self.on_start(context, **kwargs)
        self._state = new_state

        try:
            # run if
            # 1. task record is inited. or
            # 2. checkpoint connection is not specified
            if self._state == self.STATE_EXECUTING:
                context.on_task_start(self)
                self._result = self.execute_internal(context, **kwargs)
                self._state = self.STATE_SUCCESS
                self.on_commit(context)

            assert self._state == self.STATE_SUCCESS
            self._result_code = self.RET_CODE_SUCCESS
            context.on_task_success(self)

        except Exception as e:
            logger(exec=self.flow_id, flow=self._flow, task=self.name).exception(str(e))
            self._state = self.STATE_FAILED
            self._result_code = self.RET_CODE_FAIL
            self._result = e
            self.on_rollback(context)
            context.on_task_failed(self, e)

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

    def dispose(self):
        self._result = None
        self._attributes = None

    @property
    def info(self):
        return {
            'name': self.name,
            'class': type(self).__name__,
            'module': type(self).__module__,
            'bases': [x.__module__ + '.' + x.__name__ for x in type(self).__bases__],
            # 'attrs': list(filter(lambda x: x not in dir(Task) and not x.startswith('_'), dir(task)))
            'attrs': list(filter(lambda x: not x.startswith('_'), dir(self)))
        }


class ETLTask(Task):
    DEFAULT_CHECKPOINT = '1970-01-01 00:00:00'

    ATTR_LAST_CHECKPOINT = 'LAST_CHECKPOINT'
    ATTR_CHECKPOINT = 'CHECKPOINT'

    def __init__(self):
        Task.__init__(self)

        self.set_attribute(self.ATTR_LAST_CHECKPOINT, self.DEFAULT_CHECKPOINT)
        now_ts = int(time.time())
        init_ts = datetime_str_to_timestamp(self.DEFAULT_CHECKPOINT, tz=self.checkpoint_timezone)
        checkpoint_ts = now_ts - (now_ts - init_ts) % self.checkpoint_round
        self.set_attribute(self.ATTR_CHECKPOINT, timestamp_to_datetime(checkpoint_ts).strftime('%Y-%m-%d %H:%M:%S'))

    def on_pending(self, context):
        Task.on_pending(self, context)

        # 基于当前时间,进行粒度对齐后计算本次执行的checkpoint
        now_ts = int(time.time())
        init_ts = datetime_str_to_timestamp(self.DEFAULT_CHECKPOINT, tz=self.checkpoint_timezone)
        checkpoint_ts = now_ts - (now_ts - init_ts) % self.checkpoint_round
        self.set_attribute(self.ATTR_CHECKPOINT, timestamp_to_datetime(checkpoint_ts).strftime('%Y-%m-%d %H:%M:%S'))

        last_record = context.sys_recorder.last_success_record(self.name)
        if last_record:
            last_attrs = json.loads(last_record['attributes'])
            self.set_attribute(self.ATTR_LAST_CHECKPOINT, last_attrs[self.ATTR_CHECKPOINT])

    @property
    def _last_checkpoint(self):
        return self._attributes.get(self.ATTR_LAST_CHECKPOINT)

    @property
    def _checkpoint(self):
        return self._attributes.get(self.ATTR_CHECKPOINT)

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

    def on_start(self, context, **kwargs):
        force = kwargs.get('force', False)

        if self._checkpoint > self._last_checkpoint or force:
            return self.STATE_EXECUTING
        # 重复执行就直接跳过
        logger(exec=self.flow_id, flow=self._flow, task=self.name).warn('last checkpoint {} indicates the task {} is already executed, bypass the execution'.format(
            self._last_checkpoint, self.name))

        return self.STATE_SUCCESS

    def on_commit(self, context, **kwargs):
        target_df = self._result

        enable_stdout = context.conf['pipe.stdout'] if context.conf.has('pipe.stdout') else False

        if enable_stdout and not sys.stdout.isatty():
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

        kw = self._check_target()

        target_conn.store(target_df, self.target_table,
                          if_exists=self.target_mode,
                          chunksize=kwargs.get('chunksize', 10000),
                          typehints=self.target_typehints,
                          checkpoint=self._checkpoint,
                          last_checkpoint=self._last_checkpoint,
                          checkpoint_column=self.target_checkpoint_column,
                          pkey=self.target_pkey,
                          indexes=indexes,
                          **kw)

    def _check_target(self):
        """
        自定义target属性, `target_%s`
        """
        kw = {}
        exclude_attrs = [attr for attr in ETLTask.__dict__.keys() if attr.startswith('target_')]

        for key in self.__class__.__dict__.keys():
            if key.startswith('target_') and key not in exclude_attrs:
                name = key.split('_', 1)[-1]
                kw[name] = getattr(self, key)
        return kw


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
        """
        the single source (table/query) to process etl
        :return:
        """
        raise NotImplementedError("The source is required")

    @property
    def is_source_query(self):
        """
        whether the source is query or not (table)
        :return:
        """
        return True

    def transform(self, df):
        """
        process to transform the source dataframe to another one
        :return:
        """
        return df

    def execute_internal(self, context, **kwargs):
        source_conn = context.get_connection(self.source_conn)
        assert isinstance(source_conn, Connection)
        enable_stdin = bool(context.conf.get_or_else('pipe.stdin', False))
        if enable_stdin:
            df = pd.read_json(sys.stdin, orient='records') if not sys.stdin.isatty() else source_conn.load_query(
                self.source) if self.is_source_query else source_conn.load(self.source)
        else:
            df = source_conn.load_query(self.source) if self.is_source_query else source_conn.load(self.source)
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


class Flow(object):

    STATE_EXECUTING = (2, 'Executing')[0]
    STATE_SUCCESS = (3, 'Succeeded')[0]
    STATE_FAILED = (4, 'Failed')[0]

    def __init__(self, name, tasks, deps=None):
        self.name = name
        self.tasks = tasks
        self.deps = deps if deps else {}
        self.forest = self.validate()

    def __repr__(self):
        return self.name + ": tasks=" + self.tasks.__repr__() + ", deps=" + self.deps.__repr__()

    def validate(self):
        """
        util method to build flow forest
        :param tasks: the specified tasks to form the flow
        :return: the tasks are not dependent by others
        """
        assert (self.name not in self.tasks), 'flow name conflict with some tasks'

        task_roots = dict()
        for task in self.tasks:
            if task in self.deps:
                for dep in self.deps[task]:
                    task_roots[dep] = task

        forests = set(filter(lambda t: t not in task_roots, self.tasks))
        return forests

    def uniform(self):
        if len(self.forest) > 1:
            self.tasks.append(self.name)
            self.deps[self.name] = self.forest
        return self

    def dump(self, name=None, prefix='', tail=True, root=True):
        if not name:
            name = self.name
        if root:
            print(prefix + ' ' + name)
        else:
            print(prefix + ("└── " if tail else "├── ") + name)
        children = list(self.deps[name] if name in self.deps else [])

        if len(children) > 0:
            last_child = children[-1]
            children = children[0: -1]
            for child in children:
                self.dump(child, prefix + ("    " if tail else "│   "), False, False)
            self.dump(last_child, prefix + ("    " if tail else "│   "), True, False)

    def to_dict(self):
        return {
            'name': self.name,
            'tasks': self.tasks,
            'deps': dict([(t, list(d)) for (t, d) in self.deps.items()])
        }
