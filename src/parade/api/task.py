from flask import current_app, make_response
from flask_restful import Resource, Api

from .result import Result
from ..core.engine import Engine
from ..core.task import APITask
from . import api
from ..utils.log import logger

api = Api(api, catch_all_404s=True)


class TaskAPI(Resource):
    """
    The api blue
    print to execute etl task
    """

    def __init__(self):
        app_name = current_app.name
        app_context = current_app.config[app_name]

        self.engine = Engine(app_context)

    def post(self, task_key):
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

        self._process(task_key, **task_args)

    def get(self, task_key):
        # data in string format and you have to parse into dictionary
        from flask import request
        task_args = dict(map(lambda x: (x[0], x[1][0]), filter(lambda x: len(x[1]) == 1, dict(request.args).items())))

        self._process(task_key, **task_args)

    def _process(self, task_key, **kwargs):
        raw_result, attrs = self.engine.execute(task_key, **kwargs)
        result = Result.builder().set_data(raw_result).set_attrs(attrs).build()

        export_type = kwargs.get("_export", None)
        export_name = kwargs.get("_filename", None)
        compact = kwargs.get("_compact", None)

        if export_type is not None:
            export_labels = result.attrs.get(APITask.ATTR_EXPORT_LABELS, {})
            export_io = result.export(export_type, export_name, for_web=True, labels=export_labels)
            file_contents = export_io.getvalue()
            response = make_response(file_contents)
            response.headers["Content-Disposition"] = "attachment; filename=" + str(export_name)
            return response

        view_labels = result.attrs.get(APITask.ATTR_VIEW_LABELS, {})
        if compact is not None:
            return result.content(labels=view_labels)

        resp = {"code": 200, "content": result.content(labels=view_labels), "message": "OK"}
        resp.update(result.attrs)
        return resp


api.add_resource(TaskAPI, '/api/task/<task_key>')
