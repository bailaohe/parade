from flask import request
from flask_restful import Api, reqparse

from . import parade_blueprint, ParadeResource, catch_parade_error
from parade.core.engine import Engine

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

    @catch_parade_error
    def get(self):
        # parser.add_argument('executing', type=bool)
        # args = parser.parse_args()
        executing = request.args.get('executing', type=bool, default=None)
        flow = request.args.get('flow', default=None)
        page_size = request.args.get('pageSize', type=int, default=0)
        page_no = request.args.get('pageNo', type=int, default=1)
        return self.context.sys_recorder.load_flows(flow=flow, executing=executing, page_size=page_size,
                                                    page_no=page_no)


class ExecDetailAPI(ParadeResource):
    @catch_parade_error
    def get(self, id):
        executing_flow = self.context.sys_recorder.load_flow_by_id(id)
        exec_tasks = self.context.sys_recorder.load_flow_tasks(id)
        flow = self.context.get_flowstore().load(executing_flow['flow']).uniform()

        result = {
            'flow': flow.to_dict(),
            'exec': {
                'flow': executing_flow,
                'tasks': exec_tasks
            }
        }
        return result


class JobLogAPI(ParadeResource):
    @catch_parade_error
    def get(self, exec_id, task):
        import os
        logfile = os.path.join('executing', exec_id, 'tasks', task)

        log_lines = []
        if os.path.exists(logfile):
            with open(logfile, 'r') as f:
                log_lines = f.readlines()

        return log_lines


api.add_resource(ExecAPI, '/api/exec')
api.add_resource(ExecDetailAPI, '/api/exec/<id>')
api.add_resource(JobLogAPI, '/api/exec/<exec_id>/<task>')
