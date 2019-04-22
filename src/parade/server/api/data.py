import json

from flask import request, make_response
from flask_restful import Api, reqparse

from . import parade_blueprint, ParadeResource, catch_parade_error
from parade.connection.localfile import LocalFile
from parade.core.task import ETLTask

import pandas as pd

api = Api(parade_blueprint, catch_all_404s=True)
parser = reqparse.RequestParser()


class DataAPI(ParadeResource):
    """
    The api blue print to execute etl task
    """

    @catch_parade_error
    def get(self, name):
        # data in string format and you have to parse into dictionary
        data_task = self.context.get_task(name, task_class=ETLTask)
        return data_task.info

    @catch_parade_error
    def post(self, name):
        # data in string format and you have to parse into dictionary
        complete = request.args.get('complete', type=bool, default=False)
        export = request.args.get('export', default=None)

        task_args = request.get_json() or {}
        data_task = self.context.get_task(name, task_class=ETLTask)

        df = data_task.execute_internal(self.context, **task_args)

        if export:
            export_io, export_file = LocalFile.export(df, name, export_type=export)
            response = make_response(export_io.getvalue())
            response.headers["Content-Disposition"] = "attachment; filename=" + str(export_file)
            return response

        if isinstance(df, pd.DataFrame):
            data = json.loads(df.to_json(orient='records'))
        else:
            data = df
        return dict({'data': data}, **data_task.attributes) if complete else data


api.add_resource(DataAPI, '/api/data/<name>')
