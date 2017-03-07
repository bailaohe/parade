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


class Connection(object):
    """
    The connection object, which is opened with data source and its implementation is also
    related to the context
    """

    def __init__(self, datasource):
        self.datasource = datasource

    def load(self, table, **kwargs):
        raise NotImplementedError

    def load_query(self, query, **kwargs):
        raise NotImplementedError

    def store(self, df, table, **kwargs):
        raise NotImplementedError

    @property
    def accept(self):
        raise NotImplementedError

    """
        -- mysql dialect
    CREATE TABLE _task_record (
        `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
        `task` varchar(64) NOT NULL,
        `checkpoint` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
        `create_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
        `commit_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
        `update_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        `status` int(11) NOT NULL DEFAULT 0, -- 0: running, 1: committed, 2: failed
        `message` varchar(256) NOT NULL DEFAULT 'OK',
         PRIMARY KEY (`id`),
         KEY `idx_task_create` (`task`,`create_time`)
    );

    -- postgresql dialect
    CREATE TABLE public._task_record (
        id SERIAL PRIMARY KEY NOT NULL,
        task CHARACTER VARYING(64) NOT NULL,
        checkpoint TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT now(),
        create_time TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT now(),
        commit_time TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT now(),
        update_time TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT now(),
        status INTEGER NOT NULL DEFAULT 0,
        message CHARACTER VARYING NOT NULL DEFAULT 'OK'::character varying
    );
    CREATE INDEX idx_task_create ON _task_record USING BTREE (task, create_time);
    """

    @property
    def can_produce(self):
        raise NotImplementedError

    def last_record(self, task_name):
        raise NotImplementedError

    def create_record(self, task_name, new_checkpoint):
        raise NotImplementedError

    def commit_record(self, txn_id):
        raise NotImplementedError

    def rollback_record(self, txn_id, err):
        raise NotImplementedError
