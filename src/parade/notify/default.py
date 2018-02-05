from . import Notifier
from ..utils.log import parade_logger as logger


class ParadeNotifier(Notifier):
    """
    This is *JUST A PLACEHOLDER* implementation
    """
    def notify_error(self, task, reason, **kwargs):
        logger.error('task {task} failed: {reason}'.format(task=task, reason=reason))

    def notify_success(self, task, **kwargs):
        logger.error('task {task} succeeded'.format(task=task))
