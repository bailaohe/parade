from ..core import Plugin


class Notifier(Plugin):
    """
    The notifier to notify task event (success/fail)
    """

    def notify_success(self, task, **kwargs):
        """
        schedule the task-flow
        :param dag_key: the flow name
        :param cron: the cron string to schedule the flow
        :return:
        """
        raise NotImplementedError

    def notify_error(self, task, reason, **kwargs):
        """
        unschedule the task-flow
        :param flow_name: the flow name
        :return:
        """
        raise NotImplementedError

