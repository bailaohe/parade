import copy

from ..core import Plugin
from ..utils.misc import merge_dict
from collections import defaultdict


class ConnConf(object):
    """
    The data source object. The object does not maintain any stateful information.
    """

    def __init__(self, driver, **kwargs):
        self.driver = driver
        self.attributes = defaultdict(**kwargs)

    @property
    def protocol(self):
        return self.attributes.get('protocol', None)

    @property
    def host(self):
        return self.attributes.get('host', None)

    @property
    def port(self):
        return self.attributes.get('port', None)

    @property
    def user(self):
        return self.attributes.get('user', None)

    @property
    def password(self):
        return self.attributes.get('password', None)

    @property
    def db(self):
        return self.attributes.get('db', None)

    @property
    def ds(self):
        return self.attributes.get('ds', None)

    @property
    def uri(self):
        return self.attributes.get('uri', None)


class Connection(Plugin):
    """
    The connection object, which is opened with data source and its implementation is also
    related to the context
    """
    settings = None

    def initialize(self, context, conf):
        Plugin.initialize(self, context, conf)

        conf_dict = conf.to_dict()
        self.settings = ConnConf(**conf_dict)

    def load(self, table, **kwargs):
        raise NotImplementedError

    def load_query(self, query, **kwargs):
        raise NotImplementedError

    def store(self, df, table, **kwargs):
        raise NotImplementedError
