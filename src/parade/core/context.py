from collections import defaultdict

from ..core.task import Task
from ..utils.modutils import get_class, iter_classes
from ..connection import Connection, Datasource
from ..notify import Notify


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
        self.task_dict = self._get_tasks()

    def setup(self):
        raise NotImplementedError

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
        return self._get_tasks().keys()

    def get_connection(self, conn_key):
        """
        Get the connection with the connection key
        :param conn_key: the key of the connection
        :return: the connection instance
        """

        if conn_key not in self._conn_cache:
            conn_conf = self.conf['connection']
            assert conn_key in conn_conf.to_dict(), 'connection {} is not configured'.format(conn_key)
            datasource = Datasource(**conn_conf[conn_key].to_dict())
            conn_cls = get_class(datasource.driver, Connection, 'parade.connection', self.name + '.contrib.connection')
            if conn_cls:
                self._conn_cache[conn_key] = conn_cls(datasource)

        if conn_key not in self._conn_cache:
            raise NotImplementedError("The connection [{}] initialization failed".format(conn_key))

        return self._conn_cache[conn_key]

    def get_checkpoint_connection(self):
        if not self.conf.has('checkpoint.connection'):
            return None
        checkpoint_conn_key = self.conf['checkpoint.connection']
        return self.get_connection(checkpoint_conn_key)

    def get_notifier(self):
        """
        Get the notifier with the notify key
        :param notify_key: the key of the notifier
        :return: the notifier instance
        """

        if not self.conf.has('notify'):
            return None

        if not self._notifier:
            notify_conf = self.conf['notify']
            assert 'driver' in notify_conf.to_dict(), 'no driver provided in notify section'
            driver = notify_conf['driver']
            assert driver in notify_conf.to_dict(), 'no driver {} provided in notify section'.format(driver)

            notifier_cls = get_class(driver, Notify, 'parade.notify', self.name + '.contrib.notify')
            if notifier_cls:
                self._notifier = notifier_cls(notify_conf[driver])

        return self._notifier
