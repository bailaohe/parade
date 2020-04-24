import os
import sys
import yaml


def inside_workspace():
    return bool(locate_bootstrap())


def locate_bootstrap():
    """Return the path to the closest parade bootstrap file in current directory
    """
    clue = os.environ.get('PARADE_WORKSPACE', '.')
    path = os.path.abspath(clue)
    bootfile = os.path.join(path, 'parade.bootstrap.yml')
    if os.path.exists(bootfile):
        return bootfile
    return None


def load_bootstrap(addpath=True):
    """Initialize environment to use command-line tool from inside a project
    dir. This sets the Scrapy settings module and modifies the Python path to
    be able to locate the project module.
    """
    bootfile = locate_bootstrap()
    if not bootfile:
        return []
    workspace = os.path.dirname(bootfile)
    if addpath and workspace not in sys.path:
        sys.path.append(workspace)
    with open(bootfile) as f:
        content = f.read()
        config_dict = yaml.load(content, Loader=yaml.FullLoader)
        config_dict['workspace']['path'] = workspace
        return config_dict
    return []
