from . import DAGStore
from ..utils.log import logger


class ParadeDAGStore(DAGStore):
    """
    This is *JUST A PLACEHOLDER* implementation
    """

    def create(self, *tasks, cron=None, dag_key=None):
        logger.warn('This is JUST-A-PLACEHOLDER, no dag is created')
        return None

    def delete(self, flow_name):
        pass

