from . import ParadeCommand
from ..core.engine import Engine
from ..utils.log import logger


class ExecCommand(ParadeCommand):
    """
    The exec command to run a flow or a set tasks,
    if the tasks to execute have dependencies on each other,
    parade will handle them correctly
    """
    requires_workspace = True

    def run_internal(self, context, **kwargs):
        engine = Engine(context)

        task = kwargs.get('task')
        logger.debug('prepare to execute task {}'.format(task))

        engine.execute(task)

    def short_desc(self):
        return 'execute a flow or a set of tasks'

    def config_parser(self, parser):
        parser.add_argument('task', help='the task to execute')
