from ...core.context import Context
from .. import ParadeCommand
from ...utils.log import parade_logger as logger


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
        parser.add_argument('-d', '--dep', action='append')

