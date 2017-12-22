from flask_restful import Api, reqparse

from . import parade_blueprint, ParadeResource, catch_parade_error
from ..core.engine import Engine

api = Api(parade_blueprint, catch_all_404s=True)
parser = reqparse.RequestParser()


class ExecAPI(ParadeResource):
    @catch_parade_error
    def post(self):
        parser.add_argument('flow', type=str)
        parser.add_argument('task', action='append')
        parser.add_argument('force', type=bool)
        parser.add_argument('nodep', type=bool)

        args = parser.parse_args()
        flow = args.get('flow', None)
        tasks = args.get('task', [])
        force = args.get('force', False)
        nodep = args.get('nodep', False)

        engine = Engine(self.context)
        return engine.execute_async(flow, tasks, new_thread=True, force=force, nodep=nodep)


api.add_resource(ExecAPI, '/api/exec')
