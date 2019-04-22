from .. import ParadeCommand
from ...core.engine import Engine


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

        tasks = kwargs.pop('task')
        force = kwargs.pop('force')
        nodep = kwargs.pop('nodep')

        task_args = kwargs.pop('task_arg')
        if task_args:
            for task_arg in task_args:
                arg_key, arg_val = task_arg[0].split('=')
                kwargs[arg_key] = arg_val

        return engine.execute_async(tasks=tasks, force=force, nodep=nodep, **kwargs)

    def short_desc(self):
        return 'execute a set of tasks'

    def config_parser(self, parser):
        parser.add_argument('--nodep', action="store_true", help='execute tasks without considering dependencies')
        parser.add_argument('--force', action="store_true", help='force the task to execute')
        parser.add_argument('--task-arg', action="append", nargs=1, help='the task argument')
        parser.add_argument('task', nargs='*', help='the task to schedule')
