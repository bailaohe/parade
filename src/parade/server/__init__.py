# -*- coding:utf-8 -*-
from ..core.context import Context


def _load_dash():
    pass


def init_app(context: Context, enable_dash=False):
    import os
    from flask import Flask
    from flask_cors import CORS

    template_dir = os.path.join(context.workdir, 'web')
    static_dir = os.path.join(context.workdir, 'web', 'static')

    app = Flask(context.name, template_folder=template_dir, static_folder=static_dir)
    CORS(app)

    app.parade_context = context

    from parade.server.api import parade_blueprint
    app.register_blueprint(parade_blueprint)

    if enable_dash:
        import dash
        app_dash = dash.Dash(__name__, server=app, url_base_pathname='/dash/')
        app.dash = app_dash

        _load_dash()

    return app
