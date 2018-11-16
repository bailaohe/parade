# -*- coding:utf-8 -*-
import sys
import traceback

from flask import Blueprint, current_app
from flask_restful import Resource, abort

from parade.error import ParadeError


class ParadeResource(Resource):
    """
    The api blue print to execute etl task
    """

    def __init__(self):
        self.context = current_app.parade_context


def catch_parade_error(func):
    def wrapper(*args, **kw):
        try:
            return func(*args, **kw)
        except ParadeError as e:
            if current_app.debug:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                stack_info = traceback.format_exception(exc_type, exc_value, exc_traceback)
                abort(e.status, code=e.code, message=e.reason, traceback=stack_info)
            else:
                abort(e.status, code=e.code, message=e.reason)
        except Exception as e:
            if current_app.debug:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                stack_info = traceback.format_exception(exc_type, exc_value, exc_traceback)
                abort(500, code=0, message=str(e), traceback=stack_info)
            else:
                abort(500, code=0, message=str(e))

    return wrapper


parade_blueprint = Blueprint('parade', __name__)

from . import task
from . import flow
from . import exec
from . import data
