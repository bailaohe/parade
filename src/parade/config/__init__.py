class ConfigEntry(object):
    def __init__(self, value):
        if not isinstance(value, dict):
            raise TypeError('Can only accept dict')
        self._dict = value

    def get_or_else(self, path=None, default=None):
        try:
            return self.get(path)
        except RuntimeError:
            return default

    def get(self, path=None):

        if not path:
            return self._dict

        tokens = path.split(".")

        conf_node = self._dict
        for item in tokens:
            if item not in conf_node:
                raise RuntimeError('load config [{}] failed'.format(path))
            conf_node = conf_node[item]

        if isinstance(conf_node, dict):
            return ConfigEntry(conf_node)
        return conf_node

    def has(self, path=None):
        try:
            return self.get(path) is not None
        except RuntimeError:
            return False

    def to_dict(self):
        return self._dict

    def __getitem__(self, path):
        return self.get(path)

    def __str__(self):
        return self._dict


class ConfigStore(object):
    def __init__(self, url, **kwargs):
        self.url = url
        self.kwargs = kwargs

    def load(self, app_name, profile='default', **kwargs):
        return ConfigEntry(self.load_internal(app_name, profile, **kwargs))

    def load_internal(self, app_name, profile='default', **kwargs):
        raise NotImplementedError
