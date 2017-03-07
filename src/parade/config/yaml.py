import requests
import yaml

from . import ConfigRepo


class YamlConfig(ConfigRepo):
    def load_internal(self, app_name, profile='default', **kwargs):
        """
        Load the config from a spring cloud server.
        :param app_name: the app name of the configuration
        :param profile: the profile of the configuration, e.g., the deploy environment, like `dev`, `rc`, `prod`, etc.
        :param version: the version of the configuration.
        :return: the loaded configuration object.
        """
        version = kwargs.get('version', 'master')
        uri = self.url.format(name=app_name, profile=profile, version=version)
        if uri.startswith('http://') or uri.startswith('https://'):
            r = requests.get(uri)
            if r.status_code == 200:
                return yaml.load(r.content)
        import os
        if not os.path.isabs(uri):
            workdir = self.kwargs.get('workdir', '.')
            uri = os.path.join(workdir, uri)
        with open(uri, 'r') as f:
            content = f.read()
            return yaml.load(content)

        return dict()
