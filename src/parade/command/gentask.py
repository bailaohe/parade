import re
import string
from importlib import import_module
from os.path import join, exists, abspath
from shutil import move, ignore_patterns, copy

import parade
from parade.utils.misc import copytree
from . import ParadeCommand
from ..utils.template import string_camelcase, render_templatefile


class GenTaskCommand(ParadeCommand):
    """
    The init command will create a workspace with template.
    The workspace will hold all user's work (tasks and flows)
    and customized configurations.
    """
    requires_workspace = True

    def short_desc(self):
        return 'generate a task skeleton with specified type'

    def config_parser(self, parser):
        parser.add_argument('task', nargs='*', help='the name of the task to generate')
        parser.add_argument('-t', '--task_type', dest='task_type', help='the type of the task to generate', required=True)

    @staticmethod
    def _is_valid_name(workspace_name):
        """
        check if the workspace name is valid
        :param workspace_name: the specified workspace name
        :return:
        """

        def _module_exists(module_name):
            try:
                import_module(module_name)
                return True
            except ImportError:
                return False

        if not re.search(r'^[_a-zA-Z]\w*$', workspace_name):
            print('Error: Workspace names must begin with a letter and contain' \
                  ' only\nletters, numbers and underscores')
        elif _module_exists(workspace_name):
            print('Error: Module %r already exists' % workspace_name)
        else:
            return True
        return False

    def run_internal(self, context, **kwargs):
        task_names = kwargs['task']
        task_type = kwargs['task_type']

        target_path = join(context.workdir, context.name, "task")

        source_tpl = task_type + ".py.tpl"

        for task_name in task_names:
            target_tpl = task_name + ".py"

            source_tplfile = join(self.templates_dir, source_tpl)
            target_tplfile = join(target_path, target_tpl)
            copy(source_tplfile, target_tplfile)

            render_templatefile(target_tplfile, TaskName=string_camelcase(task_name))

    @property
    def templates_dir(self):
        _templates_base_dir = join(parade.__path__[0], 'template')
        return join(_templates_base_dir, 'task')

