import threading
from concurrent.futures import ThreadPoolExecutor

from tornado import gen, queues, ioloop

from ..utils.log import logger


class Engine(object):
    """
    An engine to execute etl tasks at runtime. The engine is initialized by an ETL executor context.
    """

    def __init__(self, context, detach=False):
        """
        Initialize the Engine with the executor context
        :param context: the parade context to boot engine
        :param detach: the flag to indicate the engine is executed in detached mode or not
        :return: the initialized engine
        """
        self.context = context

        # the thread pool to convert block execution of task into async process
        self.thread_pool = ThreadPoolExecutor(4)
        self.wait_queue = queues.Queue()
        self.exec_queue = queues.Queue()

        def engine_loop():
            _ioloop = ioloop.IOLoop.current()
            _ioloop.add_callback(self.daemon_loop)
            _ioloop.start()

        # if the detached mode is enabled
        # use a seperated thread to boot the io-loop
        self.loop_thread = None
        if detach:
            logger.debug("engine running in detach mode")
            self.loop_thread = threading.Thread(target=engine_loop)
            self.loop_thread.start()

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
        result = task.execute(self.context, **kwargs)
        return result, task.attributes

    def execute_dag(self, *task_names):
        """
        execute a set of tasks with DAG-topology into consideration
        :param task_names: the tasks to form DAG
        :return:
        """
        self.submit_dag(*task_names)
        io_loop = ioloop.IOLoop.current()
        io_loop.run_sync(self.execute_dag_ioloop)

    def submit_dag(self, *task_names):
        for task_name in task_names:
            assert task_name in self.context.task_dict, 'task {} not found'.format(task_name)

        # add to wait queue, waiting to execute
        self.wait_queue.put(set(task_names))

    @gen.coroutine
    def daemon_loop(self):
        yield self.execute_dag_ioloop()

    @gen.coroutine
    def execute_dag_ioloop(self):
        """
        the async process to execute task DAG
        :return:
        """
        executing, done = set(), set()

        @gen.coroutine
        def _produce_tasks():
            """
            the inner async procedure of task producer
            :return:
            """
            # wait until all tasks in executing queue are done
            yield self.exec_queue.join()

            # reset the *executing* and *done* set
            executing.clear()
            done.clear()

            # retrieve the task-DAG from wait-queue to exec-queue
            sched_task_names = yield self.wait_queue.get()
            for sched_task_name in sched_task_names:
                self.exec_queue.put(sched_task_name)
            self.wait_queue.task_done()

        @gen.coroutine
        def _consume_task():
            """
            the inner async procedure of task consumers
            :return:
            """
            next_task_name = yield self.exec_queue.get()
            logger.debug("pick up task [{}] ...".format(next_task_name))
            try:
                if next_task_name in executing:
                    logger.debug("task [{}] is executing, pass ...".format(next_task_name))
                    return

                next_task = self.context.task_dict[next_task_name]
                task_deps = next_task.deps
                # if len(task_deps) > 0:
                #     logger.debug(
                #         "task [{}] has {} dependant task(s), {}".format(next_task_name, len(task_deps), task_deps))
                done_deps = set(filter(lambda x: x in done, task_deps))

                if len(task_deps) == len(done_deps):
                    # all dependencies are done
                    # submit the task to threading pool to execute
                    if len(task_deps) > 0:
                        logger.debug("all dependant task(s) of task {} is done".format(next_task_name))
                    executing.add(next_task_name)

                    logger.debug("task {} start executing ...".format(next_task_name))
                    yield self.thread_pool.submit(next_task.execute, self.context)
                    logger.debug("task {} Executed successfully".format(next_task_name))
                    done.add(next_task_name)

                else:
                    # otherwise, re-put the task into the end of the queue
                    # sleep for 1 second
                    self.exec_queue.put(next_task_name)
                    yield gen.sleep(1)
            except Exception as e:
                logger.exception(str(e))
            finally:
                self.exec_queue.task_done()

        @gen.coroutine
        def consumer():
            while True:
                yield _consume_task()

        @gen.coroutine
        def producer():
            while True:
                yield _produce_tasks()

        for _ in range(2):
            consumer()

        # we use a single producer within the main-thread
        producer()

        yield self.exec_queue.join()
        assert executing == done
