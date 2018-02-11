import copy

from ..utils.modutils import get_class
from ..core import Plugin


class ConfigEntry(object):
    def __init__(self, value=None, prefix=None):
        if not value:
            value = {}
        if not isinstance(value, dict):
            raise TypeError('Can only accept dict')
        self._dict = value
        self.prefix = prefix

    def put(self, path, value):
        assert path is not None
        assert value is not None
        assert isinstance(path, str)
        # assert isinstance(value, str)

        paths = path.split('.')

        node = self._dict
        for i in range(len(paths) - 1):
            if paths[i] not in node:
                node[paths[i]] = {}
            node = node[paths[i]]
        node[paths[-1]] = value

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
            return ConfigEntry(conf_node, path if not self.prefix else self.prefix + '.' + path)
        return conf_node

    def has(self, path=None):
        try:
            return self.get(path) is not None
        except RuntimeError:
            return False

    def traverse(self):
        stack = [([], self._dict)]
        results = {}
        while len(stack) > 0:
            keys, val = stack.pop()

            if isinstance(val, dict):
                for (k, v) in val.items():
                    stack.append((keys + [k], v))

            else:
                results['.'.join(keys)] = val

        return results

    def to_dict(self):
        return self._dict

    def __getitem__(self, path):
        return self.get(path)

    def __str__(self):
        return self._dict.__str__()


class ConfigParser(object):
    def parse(self, raw_conf, **kwargs):
        raise NotImplementedError


class ConfigStore(Plugin):
    def load(self, **kwargs):
        import os
        config_name = self.conf['name']
        config_profile = self.conf['profile']

        config_profile = os.environ.get('PARADE_PROFILE', config_profile)

        raw_conf = self.load_internal(config_name, profile=config_profile)
        conf = copy.deepcopy(raw_conf)
        if self.conf.has('parser'):
            parser_driver = self.conf['parser']
            parser_cls = get_class(parser_driver, ConfigParser, self.context.name + '.contrib.config')
            config_parser = parser_cls()
            conf = config_parser.parse(raw_conf, profile=config_profile)

        return ConfigEntry(conf)

    def load_internal(self, name, profile='default', **kwargs):
        raise NotImplementedError
