from flask_restful import Api

from . import parade_blueprint, ParadeResource, catch_parade_error

api = Api(parade_blueprint, catch_all_404s=True)


class TaskListAPI(ParadeResource):
    """
    The api blue print to execute etl task
    """

    def get(self):
        return list(self.context.list_tasks())


class TaskAPI(ParadeResource):
    """
    The api blue print to execute etl task
    """

    @catch_parade_error
    def get(self, task):
        task = self.context.get_task(task)

        return {
            'name': task.name,
            'class': type(task).__name__,
            'module': type(task).__module__,
            'bases': [x.__module__ + '.' + x.__name__ for x in type(task).__bases__],
            # 'attrs': list(filter(lambda x: x not in dir(Task) and not x.startswith('_'), dir(task)))
            'attrs': list(filter(lambda x: not x.startswith('_'), dir(task)))
        }


api.add_resource(TaskListAPI, '/api/task')
api.add_resource(TaskAPI, '/api/task/<task>')
