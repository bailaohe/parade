from .. import ParadeCommand


class RemoveFlowCommand(ParadeCommand):
    requires_workspace = True

    @property
    def aliases(self):
        return ['remove', 'delete', 'del']

    def run_internal(self, context, **kwargs):
        flow = kwargs.get('flow')
        flowstore = context.get_flowstore()
        flowstore.delete(flow)

    def short_desc(self):
        return 'delete the specified flow'

    def config_parser(self, parser):
        parser.add_argument('flow', help='the flow to delete')
