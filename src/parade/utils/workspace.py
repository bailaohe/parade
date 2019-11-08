import os
import sys
import yaml


def inside_workspace():
    """
    Check whether the parade is executed inside a workspace
    :return: True if parade is executed inside a workspace; False if not
    """
    return bool(locate_bootstrap())


def locate_bootstrap():
    """
    Return the path to the closest parade bootstrap file in current directory
    :return: the absolute path of bootstrap file
    """

    clue = os.environ.get('PARADE_WORKSPACE', '.')
    path = os.path.abspath(clue)
    bootfile = os.path.join(path, 'parade.bootstrap.yml')
    if os.path.exists(bootfile):
        return bootfile
    return None


def load_bootstrap(addpath=True):
    """
    Initialize environment to use command-line tool from inside a project
    dir. This sets the Parade settings module and modifies the Python path to
    be able to locate the project module.

    :param addpath: the flag to add workspace into python path or not
    :return: the loaded bootstrap dict
    """
    bootfile = locate_bootstrap()
    if not bootfile:
        return []
    workspace = os.path.dirname(bootfile)
    if addpath and workspace not in sys.path:
        sys.path.append(workspace)
    with open(bootfile) as f:
        content = f.read()
        config_dict = yaml.load(content)
        config_dict['workspace']['path'] = workspace
        return config_dict
