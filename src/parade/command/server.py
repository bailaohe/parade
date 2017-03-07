from . import ParadeCommand


def _create_app(name, context):
    from flask import Flask
    from flask_cors import CORS

    app = Flask(name)
    CORS(app)

    app.config[name] = context

    from ..api import api as api_blueprint
    app.register_blueprint(api_blueprint)

    return app


class ServerCommand(ParadeCommand):
    requires_workspace = True

    def run_internal(self, context, **kwargs):
        port = int(kwargs.get('port', 5000))
        app = _create_app(context.name, context)

        app.run(host="0.0.0.0", port=port, debug=True)

    def short_desc(self):
        return 'start a parade api server'

    def config_parser(self, parser):
        parser.add_argument('-p', '--port', default=5000, help='the port of parade server')
