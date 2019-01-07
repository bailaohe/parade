from collections import defaultdict

from ...core.context import Context
from .. import ParadeCommand
from ...utils.log import parade_logger as logger


def _build_flow_via_package(context):
    package_task_list_dict = defaultdict(list)
    task_dict = context.load_tasks()

    for task in task_dict.values():
        package_task_list_dict[task.namespace].append(task)

    deps = dict([(task.name, task.deps) for task in context.load_tasks().values() if len(task.deps) > 0])

    for stask_name, ttaskset in deps.items():
        new_task_deps = []
        for ttask_name in ttaskset:
            stask = task_dict[stask_name]
            ttask = task_dict[ttask_name]
            if stask.namespace == ttask.namespace:
                new_task_deps.append(ttask_name)
            else:
                new_task_deps.append(ttask.namespace)
        deps[stask_name] = new_task_deps

    milestones = package_task_list_dict.keys()

    for pkg in milestones:
        pkg_tasks = [task for task_dict.values()                                                                                                                                                                                                                                                                                                                                             ]

    print('hello')



class MakeFlowCommand(ParadeCommand):

    requires_workspace = True

    @property
    def aliases(self):
        return ['new']

    def run_internal(self, context, **kwargs):
        assert isinstance(context, Context)
        deps = dict()
        flow_and_task = kwargs.get('flow_and_task')
        if len(flow_and_task) == 0:
            flow = context.name
            tasks = context.list_tasks()
            logger.info('no task provided, use detected {} tasks in workspace {}'.format(len(tasks), tasks))

            enable_package_subflow = kwargs.get('enable_package_subflow')

            if enable_package_subflow:
                _build_flow_via_package(context)

            deps = dict([(task.name, task.deps) for task in context.load_tasks().values() if len(task.deps) > 0])
        else:
            flow = flow_and_task[0]
            tasks = flow_and_task[1:]
            assert all(t in context.list_tasks() for t in tasks), 'some task in {} not found in workspace'.format(tasks)
            _deps = kwargs.get('dep')
            if _deps:
                for dep in _deps:
                    (l, r) = tuple(dep.split('->'))
                    if l not in tasks:
                        logger.error('task {} in dependencies not specified'.format(l))
                    if r not in tasks:
                        logger.error('task {} in dependencies not specified'.format(r))
                    deps[l] = deps[l] if l in deps else set(r)
                    assert isinstance(deps[l], set)
                    deps[l].add(r)

        flowstore = context.get_flowstore()
        flowstore.create(flow, *tasks, deps=deps)
        print('Flow {} created, details:'.format(flow))
        flow = flowstore.load(flow).uniform()
        print('tasks: {}'.format(flow.tasks))
        print('dependencies:')
        print('------------------------------------------')
        flow.dump()
        print('------------------------------------------')

    def short_desc(self):
        return 'create a dag (flow) with a set of tasks'

    def config_parser(self, parser):
        parser.add_argument('flow_and_task', nargs='*', help='the flow name and tasks')
        parser.add_argument('--enable-package-subflow', action="store_true",
                            help='flag to enable sub-flow creation considering package')
        parser.add_argument('-d', '--dep', action='append')

