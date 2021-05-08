from collections import defaultdict

import yaml

from .recorder import ParadeRecorder
from ..config import ConfigStore, ConfigEntry
from ..datasource import Connection, Datasource
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
        self._datasource_cache = defaultdict(Datasource)
        self._conn_cache = defaultdict(Connection)
        self._notifier = None
        self._flowstore = None
        self._flowrunner = None
        self._configstore = None

        config_settings = bootstrap['config']
        self.conf = ConfigEntry({'config': config_settings})

        self._init_configstore()
        self._reload_config()

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
        """
        load task object by name
        :param name: the task name
        :param task_class: the task class
        :return: the loaded task object
        """
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

    def get_datasource(self, ds_key):
        """
        Get the datasource with the datasource key
        :param ds_key: the key of the datasource
        :return: the datasource instance
        """

        if ds_key not in self._datasource_cache:
            ds_conf = self.conf['datasource']
            assert ds_conf.has(ds_key), 'datasource {} is not configured'.format(ds_key)
            self._datasource_cache[ds_key] = self._load_plugin('datasource', Datasource, plugin_key=ds_key)

        return self._datasource_cache[ds_key]

    def get_connection(self, conn_key):
        """
        Get the datasource with the datasource key
        :param conn_key: the key of the datasource
        :return: the datasource instance
        """

        if conn_key not in self._conn_cache:
            conn_conf = self.conf['connection']
            assert conn_conf.has(conn_key), 'connection {} is not configured'.format(conn_key)
            conn = Connection()
            conn.initialize(self, conn_conf[conn_key], conn_key)
            self._conn_cache[conn_key] = conn

        return self._conn_cache[conn_key]

    def load(self, table, conn=None, ds=None, db=None, **kwargs):
        """
        load the table data from a connection or datasource
        :param table: the table identifier
        :param conn: the connection key
        :param ds:  the datasource key
        :param db: the database
        :param kwargs: other arguments
        :return: the loaded table data in frame or dict
        """
        if conn:
            return self.get_connection(conn).load(table, **kwargs)
        if ds:
            return self.get_datasource(ds).load(table, db, **kwargs)
        raise ValueError('no connection or datasource provided')

    def load_query(self, query, conn=None, ds=None, db=None, **kwargs):
        """
        load the query data from a connection or datasource
        :param query: the query to load data
        :param conn: the connection key
        :param ds:  the datasource key
        :param db: the database
        :param kwargs: other arguments
        :return: the loaded query data in frame or dict
        """
        if conn:
            return self.get_connection(conn).load_query(query, **kwargs)
        if ds:
            return self.get_datasource(ds).load_query(query, db, **kwargs)
        raise ValueError('no connection or datasource provided')

    def store(self, df, table, conn=None, ds=None, db=None, **kwargs):
        """
        store the dataframe into the connection or datasource
        :param df: the dataframe
        :param table: the table to hold the written data
        :param conn: the connection key
        :param ds: the datasource key
        :param db: the database
        :param kwargs: other arguments
        :return: None
        """
        if conn:
            return self.get_connection(conn).store(df, table, **kwargs)
        if ds:
            return self.get_datasource(ds).store(df, table, db, **kwargs)
        raise ValueError('no connection or datasource provided')

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
        """
        the portal function to init the config store
        :return: the initialized config store
        """
        if not self._configstore:
            self._configstore = self._load_plugin('config', ConfigStore)

    def _reload_config(self):
        """
        reload the config
        :return: None
        """
        from os.path import expanduser
        home = expanduser("~")
        with open(home + '/.config/parade/default.yml', 'r') as default_config_file:
            default_conf = yaml.load(default_config_file, Loader=yaml.FullLoader)

        self.conf = self._configstore.load(default_config=default_conf)

    def _load_plugin(self, plugin_token, plugin_class, plugin_key=None, default_conf=None, package_name=None):
        """
        the portal function to load plugin object from site-path and workspace-path
        :param plugin_token: the plugin token
        :param plugin_class: the plugin class
        :param plugin_key: the identifier of the plugin
        :param default_conf: the default config
        :param package_name: the package to load plugin object
        :return: the loaded plugin
        """
        conf = default_conf

        if self.conf.has(plugin_token):
            conf = self.conf[plugin_token][plugin_key] if plugin_key else self.conf[plugin_token]
            assert conf.has('driver'), 'no driver provided in {} section'.format(plugin_token)
            driver = conf['driver']
        else:
            driver = 'default'

        plugin_package = package_name or plugin_token
        plugin_cls = get_class(driver, plugin_class, 'parade.' + plugin_package,
                               self.name + '.contrib.' + plugin_package)
        assert plugin_cls
        plugin = plugin_cls()
        plugin.initialize(self, conf, plugin_key)
        return plugin

    @property
    def sys_recorder(self):
        """
        Get the parade system datasource
        :return:
        """
        if not self.conf.has('checkpoint.connection'):
            return None
        checkpoint_conn_key = self.conf['checkpoint.connection']
        conn = self.get_connection(checkpoint_conn_key)

        try:
            return ParadeRecorder(self.name, conn)
        except Exception as e:
            logger.exception('Parade recorder initialized failed!', e)
            return None

    def on_flow_start(self, flow):
        """
        the lifecycle hook to invoke on flow start
        :param flow: the DAG to execute
        :return: the flow id
        """
        if self.sys_recorder:
            # TODO maybe we should set the flow state to `pending` here
            self.sys_recorder.init_record_tables()
            return self.sys_recorder.create_flow_record(flow.name, flow.tasks)
        return 0

    def on_flow_success(self, flow_id):
        """
        the lifecycle hook to invoke on flow done successfully
        :param flow_id: the id of the done flow
        :return: None
        """
        if self.sys_recorder:
            self.sys_recorder.mark_flow_success(flow_id)

    def on_flow_failed(self, flow_id):
        """
        the lifecycle hook to invoke on flow done failed
        :param flow_id: the id of the done flow
        :return: None
        """
        if self.sys_recorder:
            self.sys_recorder.mark_flow_failed(flow_id)

    def on_task_pending(self, task, checkpoint, flow_id, flow):
        """
        the lifecycle hook to invoke on task entering pending state
        :param task: the task name
        :param checkpoint: the checkpoint information
        :param flow_id: the context flow id
        :param flow: the context flow object
        :return: None
        """
        if self.sys_recorder:
            self.sys_recorder.init_record_tables()
            return self.sys_recorder.create_task_record(task, checkpoint, flow_id, flow)
        return 0

    def on_task_cancelled(self, task, failed_deps):
        """
        the lifecycle hook to invoke on task cancelling
        :param task: the task name
        :param failed_deps: the failed dependencies cause the cancel
        :return: None
        """
        if self.sys_recorder:
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
        """
        the lifecycle hook to invoke on task start
        :param task: the task name
        :return: None
        """
        if self.sys_recorder:
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
        """
        the lifecycle hook to invoke on task done successfully
        :param task: the task name
        :return: None
        """
        if self.sys_recorder:
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
        """
        the lifecycle hook to invoke on task done failed
        :param task: the task name
        :return: None
        """
        if self.sys_recorder:
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
