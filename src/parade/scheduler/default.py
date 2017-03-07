from . import Scheduler
from ..core.engine import Engine
from ..utils.log import logger


class ParadeScheduler(Scheduler):
    """
    The scheduler to support task-flow scheduling
    """

    def schedule(self, *tasks, cron=None, flow_name=None):
        """
        schedule the task-flow
        :param flow_name: the flow name
        :param cron: the cron string to schedule the flow
        :return:
        """
        if cron:
            raise NotImplementedError('default scheduler cannot support cron')
        engine = Engine(self.context)

        logger.debug('prepare to schedule task(s) {}'.format(tasks))

        if tasks and len(tasks) > 0:
            engine.execute_dag(*tasks)

        return None

    def unsched(self, flow_name):
        """
        unschedule the task-flow
        :param flow_name: the flow name
        :return:
        """
        pass

