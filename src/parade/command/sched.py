from ..utils.modutils import get_class, iter_classes
from ..scheduler import Scheduler
from . import ParadeCommand


class SchedCommand(ParadeCommand):

    requires_workspace = True

    def run_internal(self, context, **kwargs):
        config = context.conf
        scheduler_driver = config['scheduler.driver']
        scheduler_cls = get_class(scheduler_driver, Scheduler, 'parade.scheduler', context.name + ".contrib.scheduler")
        scheduler = scheduler_cls(context)

        tasks = kwargs.get('task')
        flow_name = kwargs.get('flow_name')
        if not flow_name:
            flow_name = context.name
        cron = kwargs.get('cron')

        scheduler.schedule(*tasks, flow_name=flow_name, cron=cron)

    def short_desc(self):
        return 'schedule a flow with a set of tasks'

    def config_parser(self, parser):
        parser.add_argument('--cron', dest='cron', help='set the schedule settings')
        parser.add_argument('--flow', dest='flow_name', help='set the flow name to schedule')
        parser.add_argument('task', nargs='*', help='the task to schedule')

