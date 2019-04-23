# -*- coding:utf-8 -*-

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
from flask_caching import Cache

from parade.core.context import Context


class Dashboard(object):

    def __init__(self, app: dash.Dash, context: Context):
        self.app = app
        self.context = context

        self.cache = Cache(app.server, config={
            # Note that filesystem cache doesn't work on systems with ephemeral
            # filesystems like Heroku.
            'CACHE_TYPE': 'filesystem',
            'CACHE_DIR': 'cache-directory',

            # should be equal to maximum number of users on the app at a single time
            # higher numbers will store more data in the filesystem / redis cache
            'CACHE_THRESHOLD': 200
        })

    @property
    def name(self):
        """
        get the identifier of the task, the default is the class name of task
        :return: the task identifier
        """
        return self.__module__.split('.')[-1]

    @property
    def display_name(self):
        return self.name

    @property
    def layout(self):
        return html.Div([html.H1('Content of dashboard [' + self.name + ']')])


class DashboardComponent(object):
    __slots__ = ('context', 'id', 'data_key',)

    def __init__(self, context, id, data_key):
        self.context = context
        self.id = id
        self.data_key = data_key

    def retrieve_data(self, **kwargs):
        data = self.context.get_task(self.data_key).execute_internal(self.context, **kwargs)
        return data

    def get_data(self, **kwargs):
        import pandas as pd
        import json
        raw_data = self.retrieve_data(**kwargs)

        if isinstance(raw_data, pd.DataFrame):
            data = json.loads(raw_data.to_json(orient='records'))
        else:
            data = raw_data

        return data

    def render_func(self, input_arg_names):
        def x_render_func(*args):
            kwargs = dict(zip(input_arg_names, args))
            output = self.get_data(**kwargs)
            return output

        return x_render_func

    @property
    def input_field(self):
        return None

    @property
    def output_field(self):
        return None

    @staticmethod
    def get_css_class(width: int):
        _column_names = [None, 'one', 'two', 'three', 'four', 'five', 'six',
                         'seven', 'eight', 'nine', 'ten', 'eleven', 'twelve']
        return _column_names[width] + ' columns'


class DashboardFilter(DashboardComponent):

    def __init__(self, context, id, data_key, auto_render=False, default_value=None, placeholder='please select ...'):
        DashboardComponent.__init__(self, context, id, data_key)
        self.auto_render = auto_render
        self.default_value = default_value
        self.placeholder = placeholder

    @property
    def input_field(self):
        return 'options'

    @property
    def output_field(self):
        return 'value'


class DashboardWidget(DashboardComponent):
    _VALID_WIDGET_TYPE = ('table', 'indicator', 'figure')

    def __init__(self, context, id, data_key, title, widget_type='table', post_processor=None, cache=None,
                 session_id='_'):
        DashboardComponent.__init__(self, context, id, data_key)
        self.title = title
        self.widget_type = widget_type
        self.cache = cache
        self.post_processor = post_processor
        self.session_id = session_id

    def pre_render(self, data):
        if self.widget_type == 'table':
            import pandas as pd
            df = pd.DataFrame.from_records(data)
            return html.Table(
                # Header
                [html.Tr([html.Th(col) for col in df.columns])] +

                # Body
                [
                    html.Tr(
                        [
                            html.Td(df.iloc[i][col])
                            for col in df.columns
                        ]
                    )
                    for i in range(len(df))
                ]
            )
        return data

    @property
    def input_field(self):
        if self.widget_type == 'figure':
            return 'figure'
        return 'children'

    def render_func(self, input_arg_names):
        def x_render_func(*args):
            kwargs = dict(zip(input_arg_names, args))
            cache = self.cache

            @cache.memoize()
            def reload_data(cache_key):
                data = self.get_data(**kwargs)
                return data

            param_key = ''
            for param in sorted(kwargs.keys()):
                if kwargs.get(param):
                    param_key += '-' + kwargs.get(param)
            output = reload_data(self.session_id + '-' + self.data_key + param_key)

            if self.post_processor:
                from importlib import import_module
                try:
                    dash_mod = import_module(self.context.name + '.dashboard')
                    output_processor = getattr(dash_mod, '_processor_' + self.post_processor)
                    output = output_processor(output)
                except Exception as e:
                    print(e)

            output = self.pre_render(output)
            return output

        return x_render_func


class SimpleDashboard(Dashboard):
    """
    SimpleDashboard adds some strong constraints to dashboard system.
    In SimpleDashboard, we assume the dashboard contains two section:
    **Filters** and **Widgets**.

    Filter section contains one or more filters to compose a filter-chain
    with the last one as **trigger**. When the trigger filter is fired,
    one or several data frame will be retrieved and cached to render
    the widget section.

    Widget section is used to layout all visualized widgets. All these
    widget is rendered with a single data frame cached and retrieved
    when trigger filter is fired.
    """

    def __init__(self, app: dash.Dash, context: Context):
        Dashboard.__init__(self, app, context)

        filter_map = {}
        for dashboard_filter in self.filters:
            if dashboard_filter:
                filter_map[dashboard_filter.id] = dashboard_filter

        self.filter_map = filter_map

        widget_map = {}
        for widget in self.widgets:
            if widget:
                widget_map[widget.id] = widget
        self.widget_map = widget_map

        self._init_callbacks()

    def _init_callbacks(self):

        def _get_component(id):
            if id in self.filter_map:
                return self.filter_map[id]
            if id in self.widget_map:
                return self.widget_map[id]
            raise ValueError('not found')

        for (output, inputs) in self.subscribes.items():
            add_callback = self.app.callback(Output(self.name + '_' + output, _get_component(output).input_field),
                                             [Input(self.name + '_' + i, _get_component(i).output_field) for (i, _) in
                                              inputs])

            arg_names = [name for (_, name) in inputs]
            add_callback(_get_component(output).render_func(arg_names))

    @property
    def layout(self):
        import uuid
        session_id = str(uuid.uuid4())
        layout = [
            html.Div([html.H1(self.display_name)]),
        ]

        if len(self.filter_placeholders) > 0:
            for row_data in self.filter_placeholders:
                assert isinstance(row_data, tuple), 'invalid row data'
                row_width = 0
                for component_width in row_data:
                    assert isinstance(component_width, int), 'invalid row data'
                    row_width = row_width + component_width
                if row_width != 12:
                    raise ValueError('row should be of width 12')

            filter_idx = 0
            for row_data in self.filter_placeholders:
                row = []
                for component_width in row_data:
                    if len(self.filters) > filter_idx:
                        dashboard_filter = self.filters[filter_idx]
                        if dashboard_filter:
                            row.append(self._render_filter_layout(dashboard_filter, component_width))
                    filter_idx += 1
                row_layout = html.Div(row, className='row', style={'marginBottom': 10})
                layout.append(row_layout)

        if len(self.widget_placeholders) > 0:
            for row_data in self.widget_placeholders:
                assert isinstance(row_data, tuple), 'invalid row data'
                row_width = 0
                for component_width in row_data:
                    assert isinstance(component_width, int), 'invalid row data'
                    row_width = row_width + component_width
                if row_width != 12:
                    raise ValueError('row should be of width 12')

            widget_idx = 0
            for row_data in self.widget_placeholders:
                row = []
                for component_width in row_data:
                    if len(self.widgets) > widget_idx:
                        widget = self.widgets[widget_idx]
                        if widget:
                            row.append(self._render_widget_layout(widget, component_width))
                    widget_idx += 1
                row_layout = html.Div(row, className='row', style={'marginBottom': 10})
                layout.append(row_layout)

        layout.append(html.Div(session_id, id='session-id', style={'display': 'none'}))

        return layout

    def _render_filter_layout(self, filter: DashboardFilter, width: int):
        return html.Div(
            dcc.Dropdown(
                id=self.name + '_' + filter.id,
                options=filter.get_data() if filter.auto_render else [{'label': '-', 'value': '-'}],
                value=filter.default_value,
                clearable=False,
                placeholder=filter.placeholder
            ),
            className=DashboardComponent.get_css_class(width)
        )

    def _render_widget_layout(self, widget: DashboardWidget, width: int):

        if widget.widget_type == 'indicator':
            return html.Div(
                [
                    html.P(
                        widget.title,
                        className="twelve columns indicator_text"
                    ),
                    html.P(
                        id=self.name + '_' + widget.id,
                        className="indicator_value"
                    ),
                ],
                className=DashboardComponent.get_css_class(width) + ' ' + 'indicator'
            )

        if widget.widget_type == 'figure':
            return html.Div(
                [
                    html.P(widget.title),
                    dcc.Graph(
                        id=self.name + '_' + widget.id,
                        style={"height": "90%", "width": "98%"},
                        config=dict(displayModeBar=False),
                    ),
                ],
                className=DashboardComponent.get_css_class(width) + ' ' + 'chart_div'
            )

        if widget.widget_type == 'table':
            return html.Div(
                [
                    html.Div(
                        id=self.name + '_' + widget.id,
                        style={
                            "maxHeight": "350px",
                            "overflowY": "scroll",
                            "padding": "8",
                            "marginTop": "5",
                            "backgroundColor": "white",
                            "border": "1px solid #C8D4E3",
                            "borderRadius": "3px"
                        }
                    )
                ],
                className=DashboardComponent.get_css_class(width)
            )

    @property
    def filter_placeholders(self):
        return []

    @property
    def widget_placeholders(self):
        return []

    @property
    def filters(self):
        return []

    @property
    def widgets(self):
        return []

    @property
    def subscribes(self):
        return {}
