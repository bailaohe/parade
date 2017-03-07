from flask import current_app
from flask_restful import Resource, Api

from . import api
from ..core.engine import Engine
from ..utils.log import logger

api = Api(api, catch_all_404s=True)


class DagAPI(Resource):
    """
    The api blue
    print to execute etl task
    """

    def __init__(self):
        app_name = current_app.name
        app_context = current_app.config[app_name]
        self.engine = Engine.instance(app_context, detach=True)

    def post(self):
        # data in string format and you have to parse into dictionary
        from flask import request

        try:
            task_args = request.get_json()
            if not task_args:
                task_args = {}
        except Exception as e:
            logger.exception(str(e))
            task_args = {}

        task_args_ = dict(map(lambda x: (x[0], x[1][0]), filter(lambda x: len(x[1]) == 1, dict(request.args).items())))

        if task_args_:
            task_args.update(task_args_)

        tasks = set(task_args.get('tasks', []))
        self._process(*tasks)

    def _process(self, *tasks):
        self.engine.submit_dag(*tasks)
        resp = {"code": 200, "message": "tasks {} scheduled".format(set(tasks))}
        return resp

api.add_resource(DagAPI, '/api/dag')
