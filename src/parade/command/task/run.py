from parade.command import ParadeCommand
from parade.core.engine import Engine


class ExecCommand(ParadeCommand):
    """
    The exec command to run a flow or a set tasks,
    if the tasks to execute have dependencies on each other,
    parade will handle them correctly
    """
    requires_workspace = True

    @property
    def aliases(self):
        return ['execute', 'exec']

    def run_internal(self, context, **kwargs):
        engine = Engine(context)

        tasks = kwargs.get('task')
        force = kwargs.get('force')
        nodep = kwargs.get('nodep')

        return engine.execute_async(tasks=tasks, force=force, nodep=nodep)

    def short_desc(self):
        return 'execute a set of tasks'

    def config_parser(self, parser):
        parser.add_argument('--nodep', action="store_true", help='execute tasks without considering dependencies')
        parser.add_argument('--force', action="store_true", help='force the task to execute')
        parser.add_argument('task', nargs='*', help='the task to schedule')
