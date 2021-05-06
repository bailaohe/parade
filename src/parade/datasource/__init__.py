from ..core import Plugin


class Datasource(Plugin):
    """
    The data source object. The object does not maintain any stateful information.
    """

    @property
    def protocol(self):
        return self.conf.get_or_else('protocol', None)

    @property
    def host(self):
        return self.conf.get_or_else('host', None)

    @property
    def port(self):
        return self.conf.get_or_else('port', None)

    @property
    def user(self):
        return self.conf.get_or_else('user', None)

    @property
    def password(self):
        return self.conf.get_or_else('password', None)

    @property
    def default_db(self):
        return self.conf.get_or_else('default_db', None)

    @property
    def uri(self):
        return self.conf.get_or_else('uri', None)

    def load(self, table, db, **kwargs):
        raise NotImplementedError

    def load_query(self, query, db, **kwargs):
        raise NotImplementedError

    def store(self, df, table, db, **kwargs):
        raise NotImplementedError


class Connection(Plugin):
    """
    The datasource object, which is opened with data source and its implementation is also
    related to the context
    """
    datasource = None

    def initialize(self, context, conf, key):
        Plugin.initialize(self, context, conf, key)

        if self.ds:
            self.datasource = context.get_datasource(self.ds)
        else:
            datasource = context._load_plugin('connection', Datasource, key, package_name='datasource')
            self.datasource = datasource

    @property
    def ds(self):
        return self.conf.get_or_else('ds', None)

    @property
    def db(self):
        return self.conf.get_or_else('db', None)

    def load(self, table, **kwargs):
        return self.datasource.load(table, self.db, **kwargs)

    def load_query(self, query, **kwargs):
        return self.datasource.load_query(query, self.db, **kwargs)

    def store(self, df, table, **kwargs):
        return self.datasource.store(df, table, self.db, **kwargs)
