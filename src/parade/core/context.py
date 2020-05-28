from collections import defaultdict

from .recorder import ParadeRecorder
from ..config import ConfigStore, ConfigEntry
from ..connection import Connection
from ..core.task import Task
from ..error.task_errors import DuplicatedTaskExistError
from ..flowrunner import FlowRunner
from ..flowstore import FlowStore
from ..notify import Notifier
from ..utils.log import parade_logger as logger
from ..utils.modutils import get_class, iter_classes


class Context(object):
    """
    The executor context to support the ETL job executed by the engine
    """

    def __init__(self, bootstrap):
        workspace_settings = bootstrap['workspace']

        self.name = workspace_settings['name']
        self.workdir = workspace_settings['path']

        self._task_dict = defaultdict(Task)
        self._conn_cache = defaultdict(Connection)
        self._notifier = None
        self._flowstore = None
        self._flowrunner = None
        self._configstore = None

        config_settings = bootstrap['config']
        self.conf = ConfigEntry({'config': config_settings})

        self._init_configstore()

        self.conf = self._configstore.load()

    # ========================Context as a task store=========================
    # ========================================================================
    def load_tasks(self, name=None, task_class=Task):
        """
        generate the task dict [task_key => task_obj]
        :return:
        """
        d = {}
        for task_class in iter_classes(task_class, self.name + '.task'):
            task = task_class()
            task_name = task.name
            if name and task_name != name:
                continue
            if task_name in d:
                raise DuplicatedTaskExistError(task=task_name)
            d[task_name] = task
        return d

    def get_task(self, name, task_class=Task):
        if name in self._task_dict:
            return self._task_dict[name]
        task = self.load_tasks(name, task_class=task_class)[name]
        self._task_dict[name] = task
        return task

    def list_tasks(self, task_class=Task):
        """
        get the task namelist
        :return:
        """
        return self.load_tasks(task_class=task_class).keys()

    # ========================================================================

    # ====================Context as a connection store=======================
    # ========================================================================
    def get_connection(self, conn_key):
        """
        Get the connection with the connection key
        :param conn_key: the key of the connection
        :return: the connection instance
        """

        if conn_key not in self._conn_cache:
            conn_conf = self.conf['connection']
            assert conn_conf.has(conn_key), 'connection {} is not configured'.format(conn_key)
            self._conn_cache[conn_key] = self._load_plugin('connection', Connection, plugin_key=conn_key)

        return self._conn_cache[conn_key]

    def load(self, table, conn=None, **kwargs):
        if not conn:
            raise ValueError('connection not provided')
        return self.get_connection(conn).load(table, **kwargs)

    def load_query(self, query, conn=None, **kwargs):
        if not conn:
            raise ValueError('connection not provided')
        return self.get_connection(conn).load_query(query, **kwargs)

    def store(self, df, table, conn=None, **kwargs):
        if not conn:
            raise ValueError('connection not provided')
        return self.get_connection(conn).store(df, table, **kwargs)

    # ========================================================================

    # ====================Context as other plugin store=======================
    # ========================================================================
    def get_flowstore(self):
        """
        Get the flow store
        :return: the flow store instance
        """

        if not self._flowstore:
            self._flowstore = self._load_plugin('flowstore', FlowStore)

        return self._flowstore

    def get_flowrunner(self):
        """
        Get the flow store
        :return: the flow store instance
        """

        if not self._flowrunner:
            self._flowrunner = self._load_plugin('flowrunner', FlowRunner)

        return self._flowrunner

    def _init_configstore(self):
        if not self._configstore:
            self._configstore = self._load_plugin('config', ConfigStore)

    def _load_plugin(self, plugin_token, plugin_class, plugin_key=None, default_conf=None):
        conf = default_conf

        if self.conf.has(plugin_token):
            conf = self.conf[plugin_token][plugin_key] if plugin_key else self.conf[plugin_token]
            assert conf.has('driver'), 'no driver provided in {} section'.format(plugin_token)
            driver = conf['driver']
        else:
            driver = 'default'

        plugin_cls = get_class(driver, plugin_class, 'parade.' + plugin_token, self.name + '.contrib.' + plugin_token)
        assert plugin_cls
        plugin = plugin_cls()
        plugin.initialize(self, conf)
        return plugin

    # ========================================================================

    @property
    def sys_recorder(self):
        """
        Get the parade system connection
        :return:
        """
        if not self.conf.has('checkpoint.connection'):
            return None
        checkpoint_conn_key = self.conf['checkpoint.connection']
        conn = self.get_connection(checkpoint_conn_key)

        try:
            return ParadeRecorder(self.name, conn)
        except:
            logger.warn('Parade recorder initialized failed!')
            return None

    def on_flow_start(self, flow):
        # TODO maybe we should set the flow state to `pending` here
        self.sys_recorder.init_record_tables()
        return self.sys_recorder.create_flow_record(flow.name, flow.tasks)

    def on_flow_success(self, flow_id):
        self.sys_recorder.mark_flow_success(flow_id)

    def on_flow_failed(self, flow_id):
        self.sys_recorder.mark_flow_failed(flow_id)

    def on_task_pending(self, task, checkpoint, flow_id, flow):
        self.sys_recorder.init_record_tables()
        return self.sys_recorder.create_task_record(task, checkpoint, flow_id, flow)

    def on_task_cancelled(self, task, failed_deps):
        self.sys_recorder.mark_task_cancelled(task.exec_id, failed_deps)

        if hasattr(self, 'webapp') and 'socketio' in self.webapp.extensions:
            socketio = self.webapp.extensions['socketio']
            socketio.emit('update', {
                'flow-id': task.flow_id,
                'task': task.name,
                'task-id': task.exec_id,
                'event': 'task-cancelled'
            }, namespace='/exec', room=str(task.flow_id))

    def on_task_start(self, task):
        self.sys_recorder.mark_task_start(task.exec_id)

        if hasattr(self, 'webapp') and 'socketio' in self.webapp.extensions:
            socketio = self.webapp.extensions['socketio']
            socketio.emit('update', {
                'flow-id': task.flow_id,
                'task': task.name,
                'task-id': task.exec_id,
                'event': 'task-started'
            }, namespace='/exec', room=str(task.flow_id))

    def on_task_success(self, task):
        self.sys_recorder.mark_task_success(task.exec_id)

        if hasattr(self, 'webapp') and 'socketio' in self.webapp.extensions:
            socketio = self.webapp.extensions['socketio']
            socketio.emit('update', {
                'flow-id': task.flow_id,
                'task': task.name,
                'task-id': task.exec_id,
                'event': 'task-succeeded'
            }, namespace='/exec', room=str(task.flow_id))

        if task.notify_success and self.get_notifier() is not None:
            self.get_notifier().notify_success(task.name)

    def on_task_failed(self, task, err):
        self.sys_recorder.mark_task_failed(task.exec_id, err)

        if hasattr(self, 'webapp') and 'socketio' in self.webapp.extensions:
            socketio = self.webapp.extensions['socketio']
            socketio.emit('update', {
                'flow-id': task.flow_id,
                'task': task.name,
                'task-id': task.exec_id,
                'event': 'task-failed'
            }, namespace='/exec', room=str(task.flow_id))

        if task.notify_fail and self.get_notifier() is not None:
            self.get_notifier().notify_error(task.name, str(err))

    def get_notifier(self):
        """
        Get the notifier with the notify key
        :return: the notifier instance
        """

        if not self._notifier:
            self._notifier = self._load_plugin('notify', Notifier)

        return self._notifier
