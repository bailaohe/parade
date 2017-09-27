from ..core import Plugin


class FlowStore(Plugin):
    """
    The flowstore to support task-flow scheduling
    """
    def create(self, flow, *tasks, deps=None, **kwargs):
        """
        schedule the task-flow
        :param dag_key: the flow name
        :param cron: the cron string to schedule the flow
        :return:
        """
        raise NotImplementedError

    def list(self):
        raise NotImplementedError

    def load(self, flow):
        raise NotImplementedError

    def delete(self, flow_name):
        """
        unschedule the task-flow
        :param flow_name: the flow name
        :return:
        """
        pass
