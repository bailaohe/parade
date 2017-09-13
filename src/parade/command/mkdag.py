from . import ParadeCommand
from ..dagstore import DAGStore
from ..utils.modutils import get_class
from ..utils.log import logger


class MakeDAGCommand(ParadeCommand):

    requires_workspace = True

    def run_internal(self, context, **kwargs):
        config = context.conf
        dagstore_driver = config['dagstore.driver']
        dagstore_cls = get_class(dagstore_driver, DAGStore, 'parade.dagstore', context.name + ".contrib.dagstore")
        dagstore = dagstore_cls(context)

        tasks = kwargs.get('task')
        dag_key = kwargs.get('flow_name')
        if not dag_key:
            dag_key = context.name
        cron = kwargs.get('cron')

        if len(tasks) == 0:
            tasks = context.list_tasks()
            logger.info('no task provided, use detected {} tasks in workspace {}'.format(len(tasks), tasks))

        dagstore.create(*tasks, dag_key=dag_key, cron=cron)

    def short_desc(self):
        return 'create a dag (flow) with a set of tasks'

    def config_parser(self, parser):
        parser.add_argument('--cron', dest='cron', help='set the schedule settings')
        parser.add_argument('--dag-key', dest='flow_name', help='set the key for the dag')
        parser.add_argument('task', nargs='*', help='the task to compose the dag')

