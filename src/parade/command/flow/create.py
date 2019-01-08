from collections import defaultdict

from parade.core.task import Flow
from .. import ParadeCommand
from ...core.context import Context
from ...utils.log import parade_logger as logger


def _build_package_flows(context):
    package_task_list_dict = defaultdict(list)
    task_dict = context.load_tasks()
    created_flow = {}

    for task_name, task in task_dict.items():
        package_task_list_dict[task.namespace].append(task_name)

    ext_deps = dict()
    deps = dict([(task.name, task.deps) for task in context.load_tasks().values() if len(task.deps) > 0])
    ext_deps.update(deps)

    legacy_ns = list(package_task_list_dict.keys()).copy()

    for task_ns in legacy_ns:
        task_ns_toks = task_ns.split('.')
        sub_task_ns = task_ns
        while len(task_ns_toks) > 0:
            task_ns_toks.pop()
            sup_task_ns = '.'.join(task_ns_toks) if len(task_ns_toks) > 0 else context.name
            if sup_task_ns not in package_task_list_dict:
                package_task_list_dict[sup_task_ns] = []
            ext_deps[sup_task_ns] = {sub_task_ns} if sup_task_ns not in ext_deps else {sub_task_ns}.union(ext_deps[sup_task_ns])
            sub_task_ns = sup_task_ns

    for stask_name, ttaskset in deps.items():
        new_task_deps = set()
        for ttask_name in ttaskset:
            stask = task_dict[stask_name]
            ttask = task_dict[ttask_name]
            if stask.namespace == ttask.namespace:
                new_task_deps = new_task_deps.union({ttask_name})
            else:
                new_task_deps = new_task_deps.union({ttask.namespace})
        ext_deps[stask_name] = new_task_deps

    milestones = package_task_list_dict.keys()

    for pkg in milestones:
        _build_sub_flow(pkg, package_task_list_dict, task_dict, ext_deps, created_flow)

    return created_flow


def _build_sub_flow(pkg, package_task_list_dict, task_dict, deps, created_flow):
    if pkg in created_flow:
        return created_flow[pkg]
    flow_tasks = set(package_task_list_dict[pkg])
    flow_deps = {pkg: flow_tasks}
    flow_milestones = set({pkg})

    if pkg in deps:
        flow_deps[pkg] = flow_deps[pkg].union(deps[pkg])
        flow_milestones = flow_milestones.union(deps[pkg])

        for spkg in deps[pkg]:
            subflow = _build_sub_flow(spkg, package_task_list_dict, task_dict, deps, created_flow)
            flow_milestones = flow_milestones.union(subflow.milestones)
            flow_tasks = flow_tasks.union(subflow.tasks)
            flow_deps.update(subflow.deps)

    # if this flow has its own tasks
    for task_name in flow_tasks:
        if task_name not in deps:
            continue
        task_deps = deps[task_name]
        flow_deps[task_name] = task_deps

        for task_dep in task_deps:
            if task_dep not in task_dict and task_dep in package_task_list_dict:
                subflow = _build_sub_flow(task_dep, package_task_list_dict, task_dict, deps, created_flow)
                flow_milestones = flow_milestones.union({task_dep}, subflow.milestones)
                flow_tasks = flow_tasks.union(subflow.tasks)
                flow_deps.update(subflow.deps)


    created_flow[pkg] = Flow(pkg, flow_tasks, flow_deps, flow_milestones)
    return created_flow[pkg]


class MakeFlowCommand(ParadeCommand):
    requires_workspace = True

    @property
    def aliases(self):
        return ['new']

    def run_internal(self, context, **kwargs):
        flowstore = context.get_flowstore()
        assert isinstance(context, Context)
        deps = dict()
        milestones = None
        flow_and_task = kwargs.get('flow_and_task')
        if len(flow_and_task) == 0:
            flow = context.name
            tasks = context.list_tasks()
            logger.info('no task provided, use detected {} tasks in workspace {}'.format(len(tasks), tasks))
            deps = dict([(task.name, task.deps) for task in context.load_tasks().values() if len(task.deps) > 0])

            enable_package_subflow = kwargs.get('enable_package_subflow')
            if enable_package_subflow:
                created_flows = _build_package_flows(context)

                for sub_flow in created_flows:
                    if sub_flow != flow:
                        flowstore.create(sub_flow, *created_flows[sub_flow].tasks, deps=created_flows[sub_flow].deps,
                                         milestones=created_flows[sub_flow].milestones)

                flow_obj = created_flows[flow]
                deps = flow_obj.deps
                milestones = flow_obj.milestones

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

        flowstore.create(flow, *tasks, deps=deps, milestones=milestones)
        print('Flow {} created, details:'.format(flow))
        flow = flowstore.load(flow)
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
