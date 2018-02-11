from github import Github

from .. import ParadeCommand


class SearchCommand(ParadeCommand):
    """
    The search command will query the prarade-contrib on github for a contributed component
    """
    requires_workspace = False

    def short_desc(self):
        return 'search a contrib component'

    def config_parser(self, parser):
        parser.add_argument('query', help='the query to lookup the contrib component')

    def run_internal(self, context, **kwargs):
        query = kwargs['query']

        g = Github('parade-user', 'parade123')
        hits = g.search_code(query, repo="bailaohe/parade-contrib", language='python', **{'in': 'path'})

        if hits.totalCount <= 0:
            print("Not found!")
        else:
            print("Found {} components:".format(hits.totalCount))
            for hit in hits:
                component_path = hit.path[0:hit.path.find('.py')]
                print(component_path)
