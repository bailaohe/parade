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

        flow = kwargs.get('flow')
        force = kwargs.get('force')

        return engine.execute_async(flow_name=flow, force=force)

    def short_desc(self):
        return 'execute a set of tasks'

    def config_parser(self, parser):
        parser.add_argument('--force', action="store_true", help='force the tasks to execute')
        parser.add_argument('flow', help='the flow to schedule')
