# -*- coding:utf-8 -*-
from ..server import start_webapp
from parade.command import ParadeCommand


class ServerCommand(ParadeCommand):
    requires_workspace = True

    def run_internal(self, context, **kwargs):
        port = int(kwargs.get('port', 5000))
        enable_dash = kwargs.get('enable_dash')
        enable_static = kwargs.get('enable_static')
        enable_socketio = kwargs.get('enable_socketio')
        start_webapp(context, port=port, enable_static=enable_static, enable_dash=enable_dash, enable_socketio=enable_socketio)

    def short_desc(self):
        return 'start a parade api server'

    def config_parser(self, parser):
        parser.add_argument('-p', '--port', default=5000, help='the port of parade server')
        parser.add_argument('--enable-static', action="store_true", help='enable static template rendering'
                                                                         'support in parade server')
        parser.add_argument('--enable-dash', action="store_true", help='enable dash support in parade server')
        parser.add_argument('--enable-socketio', action="store_true", help='enable socketio support in parade server')
