# -*- coding:utf-8 -*-
from ..server import init_app
from . import ParadeCommand


def _init_web():
    from flask import Blueprint
    web = Blueprint('web', __name__)

    @web.route("/")
    def route():
        from flask import render_template
        return render_template("index.html")

    return web


def _create_app(context):

    from flask_socketio import SocketIO

    app = init_app(context)

    web_blueprint = _init_web()
    app.register_blueprint(web_blueprint)

    socketio = SocketIO(app, async_mode='threading')
    sio = socketio.server

    @sio.on('connect', namespace='/exec')
    def connect(sid, environ):
        pass

    @sio.on('query', namespace='/exec')
    def query(sid, data):
        exec_id = data
        sio.enter_room(sid, str(exec_id), namespace='/exec')
        sio.emit('reply', exec_id, namespace='/exec')

    context.webapp = app

    return app, socketio


class ServerCommand(ParadeCommand):
    requires_workspace = True

    def run_internal(self, context, **kwargs):
        port = int(kwargs.get('port', 5000))
        enable_dash = kwargs.get('enable_dash')
        app, socketio = _create_app(context)
        debug = context.conf.get_or_else('debug', False)

        socketio.run(app, host="0.0.0.0", port=port, debug=debug, log_output=False)

    def short_desc(self):
        return 'start a parade api server'

    def config_parser(self, parser):
        parser.add_argument('-p', '--port', default=5000, help='the port of parade server')
        # parser.add_argument('--enable-dash', action="store_true", help='enable dash support in parade server')

