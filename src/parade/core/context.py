from collections import defaultdict

from ..core.task import Task
from ..utils.modutils import get_class, iter_classes
from ..connection import Connection, Datasource


class Context(object):
    """
    The executor context to support the ETL job executed by the engine
    """
    def __init__(self, name, conf, workdir=None):
        self.name = name
        self.workdir = workdir
        self.conf = conf

        self._conn_cache = defaultdict(Connection)
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
            d[task_name] = task()
        return d

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
            raise NotImplementedError("The driver [%s] is not supported".format("conn_key"))

        return self._conn_cache[conn_key]
