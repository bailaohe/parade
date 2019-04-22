# -*- coding:utf-8 -*-

import dash
import dash_html_components as html
import dash_core_components as dcc
from dash.dependencies import Input, Output

from parade.core.context import Context


class Dashboard(object):

    def __init__(self, app: dash.Dash, context: Context):
        self.app = app
        self.context = context

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
    __slots__ = ('id', 'data_key',)

    def __init__(self, id, data_key):
        self.id = id
        self.data_key = data_key

    def retrieve_data(self, context):
        data = context.get_task(self.data_key).execute_internal(context)
        return data

    def get_data(self, context):
        import pandas as pd
        import json
        raw_data = self.retrieve_data(context)

        if isinstance(raw_data, pd.DataFrame):
            data = json.loads(raw_data.to_json(orient='records'))
        else:
            data = raw_data

        return data

    @staticmethod
    def get_css_class(width: int):
        _column_names = [None, 'one', 'two', 'three', 'four', 'five', 'six',
                         'seven', 'eight', 'nine', 'ten', 'eleven', 'twelve']
        return _column_names[width] + ' columns'


class DashboardFilter(DashboardComponent):

    def __init__(self, id, data_key, auto_render=False, default_value=None, placeholder='please select ...'):
        DashboardComponent.__init__(self, id, data_key)
        self.auto_render = auto_render
        self.default_value = default_value
        self.placeholder = placeholder


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

        # widget_map = {}
        # for widget in self.widgets:
        #     if widget:
        #         widget_map[widget.id] = widget

        self._init_callbacks()


    def _init_callbacks(self):
        for output, inputs in self.subscribes:
            self.app.callback(Output(self.name + '_' + output, 'options'),
                              [Input(self.name + '_' + i) for i in inputs])()

    @property
    def layout(self):
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

        return layout

    def _render_filter_layout(self, filter: DashboardFilter, width: int):
        return html.Div(
            dcc.Dropdown(
                id=self.name + '_' + filter.id,
                options=filter.get_data(self.context) if filter.auto_render else [{'label': '-', 'value': '-'}],
                value=filter.default_value,
                clearable=False,
                placeholder=filter.placeholder
            ),
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
