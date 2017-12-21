import os

from parade.cmdline import _get_config_repo
from parade.core.context import Context
from parade.utils.workspace import load_bootstrap

_bootstrap = load_bootstrap()
_workspace_settings = _bootstrap['workspace']
_config_settings = _bootstrap['config']

_config_driver = _config_settings['driver']
_config_uri = _config_settings['uri']

_config_repo = _get_config_repo(_config_driver, _config_uri, _workspace_settings['path'])

_config_name = _config_settings['name']
_config_profile = _config_settings['profile']
_config_version = _config_settings['version']

# add this to enable switch profile via environment
_config_profile = os.environ.get('PARADE_PROFILE', _config_profile)

_config = _config_repo.load(app_name=_config_name, profile=_config_profile, version=_config_version)

_workspace = _workspace_settings['name']
_workdir = _workspace_settings['path']

context = pcxt = Context(_workspace, _config, workdir=_workdir)
