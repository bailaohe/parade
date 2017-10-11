import re
import string
from importlib import import_module
from os.path import join, exists, abspath
from shutil import move, ignore_patterns

import parade
from ..utils.misc import copytree
from . import ParadeCommand
from ..utils.template import string_camelcase, render_templatefile

TEMPLATES_TO_RENDER = (
    ('parade.bootstrap.yml',),
    ('parade.config.yml',),
)

IGNORE = ignore_patterns('*.pyc', '.svn', '.git')


class InitCommand(ParadeCommand):
    """
    The init command will create a workspace with template.
    The workspace will hold all user's work (tasks and flows)
    and customized configurations.
    """
    requires_workspace = False

    def short_desc(self):
        return 'init a workspace to work with'

    def config_parser(self, parser):
        parser.add_argument('workspace', help='the workspace to initialize')
        parser.add_argument('workdir', nargs='?', help='the directory of the workspace')

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
        project_name = kwargs['workspace']
        project_dir = project_name

        if 'workdir' in kwargs and kwargs['workdir']:
            project_dir = kwargs['workdir']

        if exists(join(project_dir, 'parade.parade.bootstrap.yml')):
            self.exitcode = 1
            print('Error: parade.parade.bootstrap.yml already exists in %s' % abspath(project_dir))
            return

        if not self._is_valid_name(project_name):
            self.exitcode = 1
            return

        copytree(self.templates_dir, abspath(project_dir), IGNORE)
        move(join(project_dir, 'module'), join(project_dir, project_name))
        for paths in TEMPLATES_TO_RENDER:
            path = join(*paths)
            tplfile = join(project_dir,
                           string.Template(path).substitute(project_name=project_name))
            render_templatefile(tplfile, project_name=project_name, project_path=abspath(project_dir),
                                ProjectName=string_camelcase(project_name))
        move(join(project_dir, 'parade.config.yml'), join(project_dir, project_name + '-default-1.0.yml'))
        print("New Parade workspace %r, using template directory %r, created in:" % \
              (project_name, self.templates_dir))
        print("    %s\n" % abspath(project_dir))
        print("You can start your first task with:")
        print("    cd %s" % project_dir)
        print("    parade gentask your_task -t etl")

    @property
    def templates_dir(self):
        _templates_base_dir = join(parade.__path__[0], 'template')
        return join(_templates_base_dir, 'workspace')
