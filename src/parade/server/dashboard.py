# -*- coding:utf-8 -*-

import dash_html_components as html
import dash
from ..core.context import Context


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
