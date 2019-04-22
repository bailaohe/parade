# -*- coding:utf-8 -*-

import dash
import dash_html_components as html

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


class DashboardFilter(DashboardComponent):
    pass


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
