import threading


class Engine(object):
    """
    An engine to execute etl tasks at runtime. The engine is initialized by an ETL executor context.
    """

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
        assert task_name in self.context.task_dict, 'task {} not found'.format(task_name)
        task = self.context.task_dict[task_name]
        task.execute(self.context, **kwargs)
        return task.result_code, task.result, task.attributes

    def execute_flow(self, flow_name, **kwargs):
        flow = self.context.get_flowstore().load(flow_name)
        flowrunner = self.context.get_flowrunner()
        if flowrunner:
            flow_id = 0
            sys_recorder = self.context.sys_recorder
            if sys_recorder:
                sys_recorder.init_record_if_absent()
                flow_id = sys_recorder.create_flow_record(flow_name, flow.tasks)

            flowrunner.submit(flow, flow_id=flow_id, **kwargs)
