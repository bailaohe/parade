from collections import defaultdict

from .recorder import ParadeRecorder
from ..flowrunner import FlowRunner
from ..connection import Connection
from ..core.task import Task
from ..flowstore import FlowStore
from ..notify import Notifier
from ..utils.modutils import get_class, iter_classes
from ..utils.log import logger


class Context(object):
    """
    The executor context to support the ETL job executed by the engine
    """

    def __init__(self, name, conf, workdir=None):
        self.name = name
        self.workdir = workdir
        self.conf = conf

        self._conn_cache = defaultdict(Connection)
        self._notifier = None
        self._flowstore = None
        self._flowrunner = None

        self.task_dict = self._get_tasks()

    def _get_tasks(self):
        """
        generate the task dict [task_key => task_obj]
        :return:
        """
        d = {}
        for task in iter_classes(Task, self.name + '.task'):
            task_name = task.__module__.split('.')[-1]
            if task_name in d:
                raise RuntimeError("Duplicated tasks with name: " + task_name)
            d[task_name] = task()
        return d

    def list_tasks(self):
        """
        get the task namelist
        :return:
        """
        return self._get_tasks().keys()

    def get_connection(self, conn_key):
        """
        Get the connection with the connection key
        :param conn_key: the key of the connection
        :return: the connection instance
        """

        if conn_key not in self._conn_cache:
            conn_conf = self.conf['connection']
            assert conn_conf.has(conn_key), 'connection {} is not configured'.format(conn_key)
            self._conn_cache[conn_key] = self.load_plugin('connection', Connection, plugin_key=conn_key)

        return self._conn_cache[conn_key]

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

    def get_notifier(self):
        """
        Get the notifier with the notify key
        :return: the notifier instance
        """

        if not self._notifier:
            self._notifier = self.load_plugin('notify', Notifier)

        return self._notifier

    def get_flowstore(self):
        """
        Get the flow store
        :return: the flow store instance
        """

        if not self._flowstore:
            self._flowstore = self.load_plugin('flowstore', FlowStore)

        return self._flowstore

    def get_flowrunner(self):
        """
        Get the flow store
        :return: the flow store instance
        """

        if not self._flowrunner:
            self._flowrunner = self.load_plugin('flowrunner', FlowRunner)

        return self._flowrunner

    def load_plugin(self, plugin_token, plugin_class, plugin_key=None, default_conf=None):
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

