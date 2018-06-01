import os
from shutil import ignore_patterns

import parade
from . import ParadeCommand
from ..utils.misc import copytree

IGNORE = ignore_patterns('*.pyc', '.svn', '.git')


class NotebookCommand(ParadeCommand):
    requires_workspace = True

    def run_internal(self, context, **kwargs):
        NotebookCommand.init_jupyter(context)
        os.system('jupyter notebook --ip=0.0.0.0 --allow-root')

    @staticmethod
    def init_jupyter(context):
        jupyter_path = os.path.join(context.workdir, '.jupyter')
        NotebookCommand._init_jupyter(jupyter_path)
        # We need set PARADE_WORKSPACE since we'll head to notebook dir
        os.environ['PARADE_WORKSPACE'] = context.workdir
        os.chdir(os.path.join(jupyter_path, 'notebook'))

    @staticmethod
    def _init_jupyter(jupyter_path):
        if not os.path.exists(jupyter_path):
            jupyter_source_dir = os.path.join(parade.__path__[0], 'template', 'workspace', 'jupyter')
            copytree(jupyter_source_dir, jupyter_path, IGNORE)

        os.environ['JUPYTER_PATH'] = jupyter_path
        os.environ['IPYTHONDIR'] = os.path.join(jupyter_path, 'ipython')

    def short_desc(self):
        return 'start a jupyter notebook server'

    def config_parser(self, parser):
        pass
