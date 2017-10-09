import asyncio
from asyncio import queues

from ..core.task import Flow
from ..error.task_errors import TaskNotFoundError
from ..flowrunner import FlowRunner
from ..utils.log import logger


class ParadeFlowRunner(FlowRunner):
    # the thread pool to convert block execution of task into async process
    wait_queue = None
    exec_queue = None
    executing_flow = None
    executing_flow_id = 0
    kwargs = {}

    def initialize(self, context, conf):
        FlowRunner.initialize(self, context, conf)

    def submit(self, flow, flow_id=0, **kwargs):
        """
        execute a set of tasks with DAG-topology into consideration
        :param task_names: the tasks to form DAG
        :return:
        """

        assert isinstance(flow, Flow)
        self.executing_flow = flow
        self.executing_flow_id = flow_id
        self.kwargs = kwargs

        for task_name in self.executing_flow.tasks:
            self.context.get_task(task_name)
        io_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(io_loop)
        self.wait_queue = queues.Queue()
        self.exec_queue = queues.Queue()
        io_loop.run_until_complete(self.execute_dag_ioloop())
        io_loop.close()

    @asyncio.coroutine
    def daemon_loop(self):
        yield from self.execute_dag_ioloop()

    @asyncio.coroutine
    def execute_dag_ioloop(self):
        """
        the async process to execute task DAG
        :return:
        """

        # add to wait queue, waiting to execute
        yield from self.wait_queue.put(set(self.executing_flow.tasks))

        executing, done = set(), set()

        @asyncio.coroutine
        def _produce_tasks():
            """
            the inner async procedure of task producer
            :return:
            """
            # wait until all tasks in executing queue are done
            yield from self.exec_queue.join()

            # reset the *executing* and *done* set
            executing.clear()
            done.clear()

            # retrieve the task-DAG from wait-queue to exec-queue
            sched_task_names = yield from self.wait_queue.get()
            for sched_task_name in sched_task_names:
                yield from self.exec_queue.put(sched_task_name)
            self.wait_queue.task_done()

        @asyncio.coroutine
        def _consume_task():
            """
            the inner async procedure of task consumers
            :return:
            """
            next_task_name = self.exec_queue.get_nowait()

            logger.info("pick up task [{}] ...".format(next_task_name))
            try:
                if next_task_name in executing:
                    logger.info("task [{}] is executing, pass ...".format(next_task_name))
                    return

                next_task = self.context.get_task(next_task_name)
                task_deps = self.executing_flow.deps.get(next_task_name, set())
                # if len(task_deps) > 0:
                #     logger.debug(
                #         "task [{}] has {} dependant task(s), {}".format(next_task_name, len(task_deps), task_deps))
                done_deps = set(filter(lambda x: x in done, task_deps))

                if len(task_deps) == len(done_deps):
                    # all dependencies are done
                    # submit the task to threading pool to execute
                    if len(task_deps) > 0:
                        logger.info("all dependant task(s) of task {} is done".format(next_task_name))
                    executing.add(next_task_name)

                    logger.info("task [{}] start executing ...".format(next_task_name))
                    # yield from self.thread_pool.submit(next_task.execute, self.context, flow_id=self.executing_flow_id,
                    #                                    flow=self.executing_flow, **self.kwargs)
                    next_task.execute(self.context, flow_id=self.executing_flow_id, flow=self.executing_flow,
                                      **self.kwargs)
                    logger.info("task [{}] Executed successfully".format(next_task_name))
                    done.add(next_task_name)

                else:
                    # otherwise, re-put the task into the end of the queue
                    # sleep for 1 second
                    yield from self.exec_queue.put(next_task_name)
                    yield from asyncio.sleep(1)
            except Exception as e:
                logger.exception(str(e))
            finally:
                self.exec_queue.task_done()

        @asyncio.coroutine
        def consumer():
            while True:
                yield from _consume_task()

        @asyncio.coroutine
        def producer():
            yield from _produce_tasks()

        # we use a single producer within the main-thread
        yield from producer()

        try:
            yield from consumer()
        except:
            pass

        yield from self.exec_queue.join()
        assert executing == done
