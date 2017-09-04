from . import ParadeCommand
from ..core.engine import Engine
from ..core.task import Task
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

        tasks = kwargs.get('task')
        force = kwargs.get('force')
        no_dag = kwargs.get('no_dag')
        logger.debug('prepare to execute tasks {}'.format(tasks))

        if len(tasks) == 0:
            tasks = list(context.list_tasks())
            logger.info('no task provided, use detected {} tasks in workspace {}'.format(len(tasks), tasks))

        if len(tasks) == 1:
            logger.info('single task {} provided, ignore its dependencies'.format(tasks[0]))
            no_dag = True

        if no_dag:
            for task in tasks:
                retcode, _, _ = engine.execute(task, force=force)
                if retcode != Task.RET_CODE_SUCCESS:
                    return retcode
        else:
            engine.execute_dag(*tasks)

        return Task.RET_CODE_SUCCESS

    def short_desc(self):
        return 'execute a flow or a set of tasks'

    def config_parser(self, parser):
        parser.add_argument('--no-dag', action="store_true", help='execute tasks without considering dependencies')
        parser.add_argument('--force', action="store_true", help='force the task to execute')
        parser.add_argument('task', nargs='*', help='the task to schedule')
