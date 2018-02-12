from os.path import join
from shutil import copy

import parade
from parade.command import ParadeCommand
from parade.utils.template import string_camelcase, render_templatefile


class GenTaskCommand(ParadeCommand):
    """
    The gentask command will create a task of specified type in current workspace
    """
    requires_workspace = True

    @property
    def aliases(self):
        return ['new']

    def short_desc(self):
        return 'generate a task skeleton with specified type'

    def config_parser(self, parser):
        parser.add_argument('task', nargs='*', help='the name of the task to generate')
        parser.add_argument('-t', '--task_type', dest='task_type', help='the type of the task to generate', required=True)

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

