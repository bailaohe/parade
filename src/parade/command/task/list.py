from parade.command import ParadeCommand


class ListTaskCommand(ParadeCommand):

    requires_workspace = True

    @property
    def aliases(self):
        return ['ls']

    def run_internal(self, context, **kwargs):
        tasks = context.list_tasks()
        print('Workspace [{}] has {} task(s):'.format(context.name, len(tasks)))
        for task_id, task in enumerate(tasks):
            print("#{}: {}".format(task_id + 1, task))

    def short_desc(self):
        return 'list the tasks created'

    def config_parser(self, parser):
        pass

