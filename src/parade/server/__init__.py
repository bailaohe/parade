# -*- coding:utf-8 -*-
from .dashboard import Dashboard
from ..utils.modutils import iter_classes
from ..core.context import Context


def load_dashboards(context, name=None):
    """
    generate the task dict [task_key => task_obj]
    :return:
    """
    d = {}
    for dash_class in iter_classes(Dashboard, context.name + '.dashboard'):
        dashboard = dash_class()
        dash_name = dashboard.name
        if name and dash_name != name:
            continue
        d[dash_name] = dashboard
    return d


def _load_dash(app, context):
    import dash_html_components as html
    import dash_core_components as dcc
    from dash.dependencies import Input, Output

    dashboards = load_dashboards(context)
    dashboard_opts = [{'label': dashkey, 'value': dashkey} for dashkey in dashboards]
    default_dashboard = None
    if len(dashboard_opts) > 0:
        default_dashboard = dashboard_opts[0]['value']

    app.layout = html.Div(
        [
            # header
            html.Div([

                html.Span("Parade Dashboard", className='app-title four columns', style={"marginTop": "8px"}),

                html.Div([
                    dcc.Dropdown(
                        id="tabs",
                        options=dashboard_opts,
                        value=default_dashboard
                    )], className="two columns", style={"marginTop": "16px"}),
                html.Div(
                    html.Img(
                        src='https://s3-us-west-1.amazonaws.com/plotly-tutorials/logo/new-branding/dash-logo-by-plotly-stripe-inverted.png',
                        height="100%")
                    , style={"float": "right", "height": "100%"})
            ],
                className="row header"
            ),

            # Tab content
            html.Div(id="tab_content", className="row", style={"margin": "2% 3%"}),

            html.Link(
                href="https://cdn.rawgit.com/plotly/dash-app-stylesheets/2d266c578d2a6e8850ebce48fdb52759b2aef506/stylesheet-oil-and-gas.css",
                rel="stylesheet"),
            html.Link(
                href="https://cdn.rawgit.com/amadoukane96/8a8cfdac5d2cecad866952c52a70a50e/raw/cd5a9bf0b30856f4fc7e3812162c74bfc0ebe011/dash_crm.css",
                rel="stylesheet"),
        ],
        className="row",
        style={"margin": "0%"},
    )

    @app.callback(Output("tab_content", "children"), [Input("tabs", "value")])
    def render_content(tab):
        if tab in dashboards:
            return dashboards[tab].layout
        else:
            return html.Div([html.H1("dashboard not found")])


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

        _load_dash(app.dash, context)

    return app
