import argparse
import sys

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
            cmd_group = None if len(cmd.__module__) == len('parade.command') + 1 + len(cmd_name) else cmd.__module__[
                len('parade.command') + 1:-len(cmd_name) - 1]
            if not cmd_group:
                d[cmd_name] = (cmd(), cmd_name, None)
            else:
                cmd_path = cmd_group + '.' + cmd_name
                d[cmd_path] = (cmd(), cmd_name, cmd_group)

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
    cmd_parsers = parser.add_subparsers(dest='command')
    cmds = _get_commands(inworkspace)

    sub_cmd_parsers_dict = {}
    for cmd, cmd_name, cmd_group in cmds.values():
        if not cmd_group:
            cmd_parser = cmd_parsers.add_parser(cmd_name, help=cmd.help())
            cmd.config_parser(cmd_parser)
        else:
            if cmd_group in sub_cmd_parsers_dict:
                sub_cmd_parsers = sub_cmd_parsers_dict[cmd_group]
            else:
                group_parser = cmd_parsers.add_parser(cmd_group, help=(cmd_group + '-related sub commands'))
                sub_cmd_parsers = group_parser.add_subparsers(dest='subcommand')
                sub_cmd_parsers_dict[cmd_group] = sub_cmd_parsers
            sub_cmd_parser = sub_cmd_parsers.add_parser(cmd_name, aliases=cmd.aliases, help=cmd.help())
            cmd.config_parser(sub_cmd_parser)
    args = parser.parse_args()

    if not args.command:
        parser.print_usage()
        return 0

    cmd_path = args.command if not hasattr(args, 'subcommand') else args.command + '.' + args.subcommand

    command = cmds[cmd_path][0]

    command_args = {}
    command_args.update(args.__dict__)

    context = None
    if inworkspace and command.requires_workspace:
        bootstrap = load_bootstrap()
        context = Context(bootstrap)

    return command.run(context, **command_args)


if __name__ == '__main__':
    retcode = execute()
    sys.exit(retcode)
