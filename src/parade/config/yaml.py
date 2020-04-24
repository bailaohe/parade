import requests
import yaml

from . import ConfigStore


class YamlConfig(ConfigStore):
    def load_internal(self, name, profile='default', **kwargs):
        """
        Load the config from a spring cloud server.
        :param profile: the profile of the configuration, e.g., the deploy environment, like `dev`, `rc`, `prod`, etc.
        :return: the loaded configuration object.
        """
        version = kwargs.get('version', '1.0')
        uri = self.conf['uri']
        uri = uri.format(name=name, profile=profile, version=version)
        if uri.startswith('http://') or uri.startswith('https://'):
            r = requests.get(uri)
            if r.status_code == 200:
                return yaml.load(r.content)
        import os
        if not os.path.isabs(uri):
            uri = os.path.join(self.context.workdir, uri)
        with open(uri, 'r') as f:
            content = f.read()
            return yaml.load(content, Loader=yaml.FullLoader)
