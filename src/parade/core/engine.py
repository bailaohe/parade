import threading
from concurrent.futures import ThreadPoolExecutor

from ..core.task import Flow
from ..error.flow_errors import FlowNotFoundError
from ..utils.log import parade_logger as logger


class Engine(object):
    """
    An engine to execute etl tasks at runtime. The engine is initialized by an ETL executor context.
    """

    thread_pool = ThreadPoolExecutor(4)

    def __init__(self, context):
        """
        Initialize the Engine with the executor context
        :param context: the parade context to boot engine
        :param detach: the flag to indicate the engine is executed in detached mode or not
        :return: the initialized engine
        """
        self.context = context

    # Global lock for creating global Engine instance
    _instance_lock = threading.Lock()

    @staticmethod
    def instance(context=None, detach=False):
        """
        the static method to get or init the singleton parade-engine
        :param context: the context to init the engine
        :param detach: the flag to indicate the engine is executed in detached mode or not
        :return:
        """
        if not hasattr(Engine, "_instance"):
            with Engine._instance_lock:
                if not hasattr(Engine, "_instance"):
                    # New instance after double check
                    assert context is not None, "no context specified"
                    Engine._instance = Engine(context, detach)
        return Engine._instance

    def execute(self, task_name, **kwargs):
        """
        execute a single task with provided arguments
        :param task_name: the task name
        :param kwargs: the arguments
        :return:
        """
        task = self.context.get_task(task_name)
        task.execute(self.context, **kwargs)
        return task.result_code, task.result, task.attributes

    def execute_async(self, flow_name=None, tasks=None, new_thread=False, force=False, nodep=False, **kwargs):
        """
        Execute a flow or a series tasks in async mode
        :param flow_name: the flow to execute
        :param tasks: the tasks to execute
        :param new_thread: do we need a new thread to handle execution
        :param force: do we need to execute without regarding to checkpoint check
        :param nodep: do we need ignore the dependencies information in tasks. Ignore this if we execute a flow rather than tasks
        :return: tuple (exec_id, last_status) for execution id of issued flow and last status
        """
        flowstore = self.context.get_flowstore()
        # prefer to execute flow at first
        if flow_name:
            flow = flowstore.load(flow_name)
            if not flow:
                raise FlowNotFoundError(flow=flow_name)
            return self._execute_flow(flow, new_thread=new_thread, force=force)

        if len(tasks) == 0:
            tasks = list(self.context.list_tasks())
            logger.info('no task provided, use detected {} tasks in workspace {}'.format(len(tasks), tasks))

        if len(tasks) == 1:
            logger.info('single task {} provided, ignore its dependencies'.format(tasks[0]))
            nodep = True

        deps = None
        if not nodep:
            deps = dict([(task.name, task.deps) for task in self.context.load_tasks().values() if len(task.deps) > 0])
        flow = Flow(self.context.name, tasks, deps)
        logger.info('Temporary flow [{}] created!'.format(flow.name))
        return self._execute_flow(flow, new_thread=new_thread, force=force, **kwargs)

    def _execute_flow(self, flow, new_thread=False, force=False, **kwargs):
        flow_id = self.context.on_flow_start(flow)
        flowrunner = self.context.get_flowrunner()

        if new_thread:
            self.thread_pool.submit(flowrunner.submit, flow, flow_id=flow_id, force=force, **kwargs)
            return flow_id
        else:
            return flowrunner.submit(flow, flow_id=flow_id, force=force, **kwargs)
