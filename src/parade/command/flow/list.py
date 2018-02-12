from .. import ParadeCommand


class ListFlowCommand(ParadeCommand):

    requires_workspace = True

    @property
    def aliases(self):
        return ['ls']

    def run_internal(self, context, **kwargs):
        flowstore = context.get_flowstore()
        flows = flowstore.list()
        print('Workspace [{}] has {} flow(s):'.format(context.name, len(flows)))
        for flow_id, flow_name in enumerate(flows):
            print("#{}: {}".format(flow_id + 1, flow_name))

    def short_desc(self):
        return 'list the flows created'

    def config_parser(self, parser):
        pass

