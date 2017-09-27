from ..core import Plugin


class FlowRunner(Plugin):
    """
    The executor to submit task flow
    """
    def submit(self, flow, flow_id=0, **kwargs):
        """
        schedule the task-flow
        :param flow: the flow to run
        :return:
        """
        raise NotImplementedError

