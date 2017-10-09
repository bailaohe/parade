from flask import request
from flask_restful import Api, abort, reqparse

from . import parade_blueprint, ParadeResource

api = Api(parade_blueprint, catch_all_404s=True)
parser = reqparse.RequestParser()


class FlowListAPI(ParadeResource):
    def get(self):
        flowstore = self.context.get_flowstore()
        return list(flowstore.list())

    def post(self):
        json = request.get_json()
        flowstore = self.context.get_flowstore()
        flowstore.create(json['name'], *json['tasks'], deps=json['deps'])



class FlowAPI(ParadeResource):
    """
    The api blue print to execute etl task
    """

    def get(self, flow):
        flow_obj = self.context.get_flowstore().load(flow)
        if not flow_obj:
            abort(404, message='Flow [{}] not found.'.format(flow))
        return {
            'name': flow_obj.name,
            'tasks': flow_obj.tasks,
            'deps': dict([(t, list(d)) for (t, d) in flow_obj.deps.items()])
        }

    def delete(self, flow):
        flow_obj = self.context.get_flowstore().load(flow)
        if not flow_obj:
            abort(404, message='Flow [{}] not found.'.format(flow))
        self.context.get_flowstore().delete(flow)
        return '', 204


api.add_resource(FlowListAPI, '/api/flow')
api.add_resource(FlowAPI, '/api/flow/<flow>')
