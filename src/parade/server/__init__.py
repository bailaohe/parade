# -*- coding:utf-8 -*-
from ..core.context import Context


def _load_dash():
    import dash_html_components as html
    import dash_core_components as dcc
    app.layout = html.Div(
        [
            # header
            html.Div([

                html.Span("CRM App using Salesforce API", className='app-title'),

                html.Div(
                    html.Img(
                        src='https://s3-us-west-1.amazonaws.com/plotly-tutorials/logo/new-branding/dash-logo-by-plotly-stripe-inverted.png',
                        height="100%")
                    , style={"float": "right", "height": "100%"})
            ],
                className="row header"
            ),

            # tabs
            html.Div([

                dcc.Tabs(
                    id="tabs",
                    style={"height": "20", "verticalAlign": "middle"},
                    children=[
                        dcc.Tab(label="Opportunities", value="opportunities_tab"),
                        dcc.Tab(label="Leads", value="leads_tab"),
                        dcc.Tab(id="cases_tab", label="Cases", value="cases_tab"),
                    ],
                    value="leads_tab",
                )

            ],
                className="row tabs_div"
            ),

            # divs that save dataframe for each tab
            html.Div(
                sf_manager.get_opportunities().to_json(orient="split"),  # opportunities df
                id="opportunities_df",
                style={"display": "none"},
            ),
            html.Div(sf_manager.get_leads().to_json(orient="split"), id="leads_df", style={"display": "none"}),
            # leads df
            html.Div(sf_manager.get_cases().to_json(orient="split"), id="cases_df", style={"display": "none"}),
            # cases df

            # Tab content
            html.Div(id="tab_content", className="row", style={"margin": "2% 3%"}),

            html.Link(href="https://use.fontawesome.com/releases/v5.2.0/css/all.css", rel="stylesheet"),
            html.Link(
                href="https://cdn.rawgit.com/plotly/dash-app-stylesheets/2d266c578d2a6e8850ebce48fdb52759b2aef506/stylesheet-oil-and-gas.css",
                rel="stylesheet"),
            html.Link(href="https://fonts.googleapis.com/css?family=Dosis", rel="stylesheet"),
            html.Link(href="https://fonts.googleapis.com/css?family=Open+Sans", rel="stylesheet"),
            html.Link(href="https://fonts.googleapis.com/css?family=Ubuntu", rel="stylesheet"),
            html.Link(
                href="https://cdn.rawgit.com/amadoukane96/8a8cfdac5d2cecad866952c52a70a50e/raw/cd5a9bf0b30856f4fc7e3812162c74bfc0ebe011/dash_crm.css",
                rel="stylesheet")
        ],
        className="row",
        style={"margin": "0%"},
    )


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
