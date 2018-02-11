import consul
import requests
import yaml

from . import ConfigStore, ConfigEntry


class ConsulConfig(ConfigStore):
    def load_internal(self, name, profile='default', **kwargs):
        """
        Load the config from a spring cloud server.
        :param profile: the profile of the configuration, e.g., the deploy environment, like `dev`, `rc`, `prod`, etc.
        :return: the loaded configuration object.
        """
        host = self.conf['host']
        token = self.conf['token']
        delim = self.conf.get_or_else('delim', '::')

        c = consul.Consul(host=host, token=token)
        prefix = 'config/' + name + delim + profile

        _, entries = c.kv.get(prefix, keys=True)
        item = ConfigEntry(prefix=prefix)
        for entry in entries:
            key = entry.replace(prefix + '/', '').replace('/', '.')
            _, val = c.kv.get(entry)
            val = val['Value']
            if val:
                item.put(key, val.decode())
        return item.to_dict()
