# -*- coding:utf-8 -*-

import dash_html_components as html


class Dashboard(object):
    @property
    def name(self):
        """
        get the identifier of the task, the default is the class name of task
        :return: the task identifier
        """
        return self.__module__.split('.')[-1]

    @property
    def layout(self):
        return html.Div([html.H1('Content of dashboard [' + self.name + ']')])
