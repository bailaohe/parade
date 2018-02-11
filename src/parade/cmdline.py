import sys
import argparse
import os

from parade.command import ParadeCommand
from parade.config import ConfigStore
from parade.core.context import Context
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
    for repo in iter_classes(ConfigStore, 'parade.config', class_filter=lambda cls: cls != ConfigStore):
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
        return 0

    command = cmds[args.command]
    command_args = args.__dict__

    context = None
    if inworkspace and command.requires_workspace:
        bootstrap = load_bootstrap()
        context = Context(bootstrap)

    return command.run(context, **command_args)


if __name__ == '__main__':
    retcode = execute()
    sys.exit(retcode)
