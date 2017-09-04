from . import Notify
from ..utils.log import logger


class ParadeNotifier(Notify):
    """
    This is *JUST A PLACEHOLDER* implementation
    """
    def notify_error(self, task, reason, **kwargs):
        logger.error('task {task} failed: {reason}'.format(task=task, reason=reason))

    def notify_success(self, task, **kwargs):
        logger.error('task {task} succeeded'.format(task=task))
