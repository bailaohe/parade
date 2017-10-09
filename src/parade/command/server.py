from . import ParadeCommand


def _create_app(context):
    from flask import Flask
    from flask_cors import CORS

    app = Flask(context.name)
    CORS(app)

    app.parade_context = context

    from ..api import parade_blueprint
    app.register_blueprint(parade_blueprint)

    return app


class ServerCommand(ParadeCommand):
    requires_workspace = True

    def run_internal(self, context, **kwargs):
        port = int(kwargs.get('port', 5000))
        app = _create_app(context)
        debug = context.conf.get_or_else('debug', False)

        app.run(host="0.0.0.0", port=port, debug=debug)

    def short_desc(self):
        return 'start a parade api server'

    def config_parser(self, parser):
        parser.add_argument('-p', '--port', default=5000, help='the port of parade server')
