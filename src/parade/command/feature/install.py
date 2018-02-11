import urllib
from os.path import join

from .. import ParadeCommand


class InstallCommand(ParadeCommand):
    """
    The install command will install acontrib component into current workspace
    """

    CONTRIB_REPO_PATH = 'https://raw.githubusercontent.com/bailaohe/parade-contrib/master/{}/{}.py'

    requires_workspace = True

    def short_desc(self):
        return 'install a contrib component into current workspace'

    def config_parser(self, parser):
        parser.add_argument('component_type',
                            help='the type of the component to install, "connection" or "flowstore" at this moment')
        parser.add_argument('component_key', help='the key of the component to install')

    def run_internal(self, context, **kwargs):
        component_type = kwargs['component_type']
        component_key = kwargs['component_key']

        install_path = join(context.workdir, context.name, "contrib", component_type)
        urllib.request.urlretrieve(InstallCommand.CONTRIB_REPO_PATH.format(component_type, component_key),
                                   join(install_path, component_key + '.py'))

