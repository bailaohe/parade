from ..core import Plugin


class Datasource(object):
    """
    The data source object. The object does not maintain any stateful information.
    """

    def __init__(self, driver, **kwargs):
        self.driver = driver
        self.attributes = kwargs

    @property
    def protocol(self):
        return self.attributes['protocol'] if 'protocol' in self.attributes else None

    @property
    def host(self):
        return self.attributes['host'] if 'host' in self.attributes else None

    @property
    def port(self):
        return self.attributes['port'] if 'port' in self.attributes else None

    @property
    def user(self):
        return self.attributes['user'] if 'user' in self.attributes else None

    @property
    def password(self):
        return self.attributes['password'] if 'password' in self.attributes else None

    @property
    def db(self):
        return self.attributes['db'] if 'db' in self.attributes else None

    @property
    def uri(self):
        return self.attributes['uri'] if 'uri' in self.attributes else None


class Connection(Plugin):
    """
    The connection object, which is opened with data source and its implementation is also
    related to the context
    """
    datasource = None

    def initialize(self, context, conf):
        Plugin.initialize(self, context, conf)
        self.datasource = Datasource(**conf.to_dict())

    def load(self, table, **kwargs):
        raise NotImplementedError

    def load_query(self, query, **kwargs):
        raise NotImplementedError

    def store(self, df, table, **kwargs):
        raise NotImplementedError
