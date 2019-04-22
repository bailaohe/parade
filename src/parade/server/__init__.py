# -*- coding:utf-8 -*-
from ..server.auth import DisabledSessionInterface, AuthManager
from .dashboard import Dashboard
from parade.core.context import Context
from parade.utils.modutils import iter_classes, walk_modules


def load_dashboards(app, context, name=None):
    """
    generate the task dict [task_key => task_obj]
    :return:
    """
    d = {}
    for dash_class in iter_classes(Dashboard, context.name + '.dashboard'):
        dashboard = dash_class(app, context)
        dash_name = dashboard.name
        if name and dash_name != name:
            continue
        d[dash_name] = dashboard
    return d


def load_contrib_apis(app, context):
    from importlib import import_module
    try:
        import_module(context.name + '.api')
    except:
        return

    for api_module in walk_modules(context.name + '.api'):
        try:
            app.register_blueprint(api_module.bp)
        except:
            pass


def _load_dash(app, context):
    import dash_html_components as html
    import dash_core_components as dcc
    from dash.dependencies import Input, Output

    dashboards = load_dashboards(app, context)
    dashboard_opts = [{'label': dashboards[dashkey].display_name, 'value': dashkey} for dashkey in dashboards]
    default_dashboard = None
    # if len(dashboard_opts) > 0:
    #     default_dashboard = dashboard_opts[0]['value']

    app.layout = html.Div(
        [
            dcc.Location(id='url', refresh=False),
            # header
            html.Div([

                html.Span("Parade Dashboard", className='app-title four columns', style={"marginTop": "8px"}),

                html.Div([
                    dcc.Dropdown(
                        id="tabs",
                        options=dashboard_opts,
                        value=default_dashboard
                    )], className="two columns", style={"marginTop": "16px"}),

                # # title content
                # html.Div(id="title_placeholder", className="two columns", style={"marginTop": "16px"}),

                html.Div(
                    html.Img(
                        src='https://res.xiaomai5.com/parade/dash-logo.png',
                        height="100%")
                    , style={"float": "right", "height": "100%"})
            ],
                className="row header"
            ),

            # Tab content
            html.Div(id="tab_content", className="row", style={"margin": "2% 3%"}),

            html.Link(
                href="https://res.xiaomai5.com/parade/stylesheet-oil-and-gas.css",
                rel="stylesheet"),
            html.Link(
                href="https://res.xiaomai5.com/parade/dash-crm.css",
                rel="stylesheet"),
        ],
        className="row",
        style={"margin": "0%"},
    )

    @app.callback(Output("tab_content", "children"),
                  [Input('url', 'pathname'),
                   Input('tabs', 'value')])
    def render_content(path, dropdown_tab):
        if not path:
            return html.Div([html.H1("Please select the dashboard")])
        path_tab = path[len('/dashboard/'):]
        if len(path_tab) == 0:
            path_tab = None

        tab = dropdown_tab or path_tab
        if tab in dashboards:
            return dashboards[tab].layout
        else:
            return html.Div([html.H1("Please select the dashboard")])


def _init_web(context, enable_auth):
    from flask import Blueprint
    from flask import render_template
    from flask_login import login_required
    import os

    web = Blueprint('web', __name__)

    template_dir = os.path.join(context.workdir, 'web')
    index_file = os.path.join(template_dir, 'index.html')
    login_file = os.path.join(template_dir, 'login.html')

    if os.path.exists(index_file):
        if enable_auth:
            @web.route("/")
            @login_required
            def route_auth():
                return render_template("index.html")
        else:
            @web.route("/")
            def route():
                return render_template("index.html")

    if os.path.exists(login_file) and enable_auth:
        @web.route("/login")
        def login():
            return render_template("login.html")

    return web


def _init_socketio(app, context):
    from flask_socketio import SocketIO
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

    socketio.init_app(app)


def _init_auth(app, context):
    app.secret_key = 'parade'
    from flask_login import LoginManager
    login_manager = LoginManager()
    login_manager.login_view = "/auth/login-view"
    login_manager.login_view = "/login"
    login_manager.init_app(app)

    if not context.conf.has('auth.driver'):
        app.auth_manager = AuthManager()
    else:
        from ..utils.modutils import get_class
        auth_cls = get_class(context.conf['auth.driver'], AuthManager, context.name + '.contrib.auth')
        app.auth_manager = auth_cls()

    @login_manager.request_loader
    def load_user_by_request(request):
        user_key = request.args.get('uid') or request.cookies.get('uid')
        auth_token = request.args.get('sid') or request.cookies.get('sid')
        return app.auth_manager.check_token(user_key, auth_token)

    app.session_interface = DisabledSessionInterface()
    from .auth import api as auth_api
    app.register_blueprint(auth_api.bp)


def start_webapp(context: Context, port=5000, enable_auth=True, enable_static=False, enable_dash=False,
                 enable_socketio=True):
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

    load_contrib_apis(app, context)

    if enable_auth:
        _init_auth(app, context)

    if enable_static or enable_dash:
        web_blueprint = _init_web(context, enable_auth)
        app.register_blueprint(web_blueprint)

    if enable_socketio:
        _init_socketio(app, context)
    context.webapp = app
    debug = context.conf.get_or_else('debug', False)

    if enable_dash:
        import dash
        app_dash = dash.Dash(__name__, server=app, url_base_pathname='/dashboard/')
        app_dash.config.suppress_callback_exceptions = True

        # force dash to work in offline mode
        app_dash.css.config.serve_locally = True
        app_dash.scripts.config.serve_locally = True

        _load_dash(app_dash, context)

        def protect_views(app):
            from flask_login import login_required
            for view_func in app.server.view_functions:
                if view_func.startswith(app.url_base_pathname):
                    app.server.view_functions[view_func] = login_required(app.server.view_functions[view_func])

            return app

        if enable_auth:
            app_dash = protect_views(app_dash)

        @app.route("/dashboard")
        def route_dash():
            import flask
            return flask.redirect('/dash')

        from werkzeug.wsgi import DispatcherMiddleware
        app = DispatcherMiddleware(app, {
            '/dash': app_dash.server
        })

        from werkzeug.serving import run_simple
        run_simple('0.0.0.0', port, app, use_reloader=True, use_debugger=debug)
    else:
        app.run(host="0.0.0.0", port=port, debug=debug)
