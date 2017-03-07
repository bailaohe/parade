import os
import sys
import argparse

from parade.config import ConfigRepo
from parade.command import ParadeCommand
from parade.utils.modutils import iter_classes
from parade.utils.workspace import inside_workspace, load_bootstrap


def _get_commands(in_workspace):
    d = {}
    for cmd in iter_classes(ParadeCommand, 'parade.command', class_filter=lambda cls: cls != ParadeCommand):
        if in_workspace or not cmd.requires_workspace:
            cmd_name = cmd.__module__.split('.')[-1]
            d[cmd_name] = cmd()
    return d


def _get_config_repo(driver, uri, workdir=None):
    for repo in iter_classes(ConfigRepo, 'parade.config', class_filter=lambda cls: cls != ConfigRepo):
        repo_name = repo.__module__.split('.')[-1]
        if repo_name == driver:
            return repo(uri, workdir=workdir)


def execute():
    # load the commands and parse arguments
    parser = argparse.ArgumentParser(description='The CLI of parade engine.')
    inworkspace = inside_workspace()
    sub_parsers = parser.add_subparsers(dest='command')
    cmds = _get_commands(inworkspace)
    for cmdname, cmd in cmds.items():
        cmd_parser = sub_parsers.add_parser(cmdname, help=cmd.help())
        cmd.config_parser(cmd_parser)
    args = parser.parse_args()

    if not args.command:
        parser.print_usage()
        sys.exit(1)

    command = cmds[args.command]
    command_args = args.__dict__

    if inworkspace and command.requires_workspace:
        bootstrap = load_bootstrap()
        workspace_settings = bootstrap['workspace']
        config_settings = bootstrap['config']

        config_driver = config_settings['driver']
        config_uri = config_settings['uri']

        config_repo = _get_config_repo(config_driver, config_uri, workspace_settings['path'])

        config_name = config_settings['name']
        config_profile = config_settings['profile']
        config_version = config_settings['version']

        # add this to enable switch profile via environment
        config_profile = os.environ.get('PARADE_PROFILE', config_profile)

        config = config_repo.load(app_name=config_name, profile=config_profile, version=config_version)

        command_args.update(workspace=workspace_settings['name'], workdir=workspace_settings['path'])
        command_args.update(config=config)

    command.run(**command_args)


if __name__ == '__main__':
    execute()
