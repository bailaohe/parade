import os
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
    from flask import Flask
    from flask_cors import CORS
    from flask_socketio import SocketIO

    template_dir = os.path.join(context.workdir, 'web')
    static_dir = os.path.join(context.workdir, 'web', 'static')

    app = Flask(context.name, template_folder=template_dir, static_folder=static_dir)
    CORS(app)

    app.parade_context = context

    from ..api import parade_blueprint
    app.register_blueprint(parade_blueprint)

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
        app, socketio = _create_app(context)
        debug = context.conf.get_or_else('debug', False)

        socketio.run(app, host="0.0.0.0", port=port, debug=debug, log_output=False)

    def short_desc(self):
        return 'start a parade api server'

    def config_parser(self, parser):
        parser.add_argument('-p', '--port', default=5000, help='the port of parade server')
