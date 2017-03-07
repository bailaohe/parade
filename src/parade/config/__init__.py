class ConfigObject(object):
    def __init__(self, value):
        if not isinstance(value, dict):
            raise TypeError('Can only accept dict')
        self._dict = value

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
            return ConfigObject(conf_node)
        return str(conf_node)

    def to_dict(self):
        return self._dict

    def __getitem__(self, path):
        return self.get(path)

    def __str__(self):
        return self._dict


class ConfigRepo(object):
    def __init__(self, url, **kwargs):
        self.url = url
        self.kwargs = kwargs

    def load(self, app_name, profile='default', **kwargs):
        return ConfigObject(self.load_internal(app_name, profile, **kwargs))

    def load_internal(self, app_name, profile='default', **kwargs):
        raise NotImplementedError
