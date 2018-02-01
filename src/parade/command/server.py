from . import ParadeCommand


def _create_app(context):
    from flask import Flask
    from flask_cors import CORS
    from flask_socketio import SocketIO

    app = Flask(context.name)
    CORS(app)

    app.parade_context = context

    from ..api import parade_blueprint
    app.register_blueprint(parade_blueprint)
    socketio = SocketIO(app, async_mode='threading')
    sio = socketio.server

    @sio.on('connect', namespace='/exec')
    def connect(sid, environ):
        pass

    @sio.on('query', namespace='/exec')
    def query(sid, data):
        exec_id = data
        sio.enter_room(sid, exec_id)
        sio.emit('reply', 'answer', namespace='/exec')

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
