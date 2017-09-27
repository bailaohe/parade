import os
from os import listdir
from os.path import isfile, join

import yaml

from ..core.task import Flow
from . import FlowStore


class ParadeFlowStore(FlowStore):
    """
    This is *JUST A PLACEHOLDER* implementation
    """

    def load(self, name):
        flow_file = os.path.join(self.flow_dir, name + '.yml')
        if os.path.exists(flow_file):
            with open(flow_file, 'r') as f:
                content = f.read()
                rawflow = yaml.load(content)
                _deps = {}
                for dep in rawflow['deps']:
                    (l, r) = tuple(dep.split('->'))
                    _deps[l] = set(r.split(','))
                flow = Flow(name, rawflow['tasks'], _deps)
                return flow
        return None

    flow_dir = None

    def initialize(self, context, conf):
        FlowStore.initialize(self, context, conf)
        self.flow_dir = join(self.context.workdir, 'flows')

    def list(self):
        return set([os.path.splitext(file)[0]
                    for file in listdir(self.flow_dir) if isfile(join(self.flow_dir, file)) and file.endswith('.yml')])

    def create(self, flow, *tasks, deps=None):
        if not deps:
            deps = {}

        Flow(flow, tasks, deps)

        dep_lines = list(map(lambda x: x[0] + '->' + ','.join(x[1]), deps.items()))
        create_flow = {
            'tasks': list(tasks),
            'deps': dep_lines
        }

        class IndentDumper(yaml.Dumper):
            def increase_indent(self, flow=False, indentless=False):
                return super(IndentDumper, self).increase_indent(flow, False)

        os.makedirs(self.flow_dir, exist_ok=True)
        flow_file = os.path.join(self.flow_dir, flow + '.yml')
        with open(flow_file, 'w') as f:
            yaml.dump(create_flow, f, Dumper=IndentDumper, default_flow_style=False)

    def delete(self, flow):
        flow_file = os.path.join(self.flow_dir, flow + '.yml')
        if os.path.exists(flow_file):
            os.remove(flow_file)
