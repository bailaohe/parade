import inspect
import os
from itertools import dropwhile

import nbformat
import sys
import six

from parade.core.task import ETLTask, SingleSourceETLTask
from parade.command.notebook import NotebookCommand
from parade.command import ParadeCommand


def get_function_body(func):
    source_lines = inspect.getsourcelines(func)[0]
    source_lines = dropwhile(lambda x: x.startswith('@'), source_lines)
    def_line = next(source_lines).strip()
    if def_line.startswith('def ') and def_line.endswith(':'):
        # Handle functions that are not one-liners
        first_line = next(source_lines)
        # Find the indentation of the first line
        indentation = len(first_line) - len(first_line.lstrip())
        return [first_line[indentation:]] + [line[indentation:] for line in source_lines]
    else:
        # Handle single line functions
        return [def_line.rsplit(':')[-1].strip()]


def get_imports(obj):
    source_lines = inspect.getsourcelines(sys.modules[obj.__module__])[0]
    source_lines = dropwhile(lambda x: x.startswith('@'), source_lines)
    import_lines = filter(lambda x: x.startswith('import ') or x.startswith('from '), source_lines)
    return list(import_lines)


class DebugCommand(ParadeCommand):
    requires_workspace = True

    def run_internal(self, context, **kwargs):
        NotebookCommand.init_jupyter(context)

        task = context.get_task(kwargs.get('task'), task_class=ETLTask)
        import_lines = get_imports(task)
        if isinstance(task, SingleSourceETLTask):
            source = task.source
            if isinstance(source, six.string_types):
                body_lines = ['source = """{}"""\n'.format(source)]
            else:
                body_lines = ['source = {}\n'.format({'a': 1})]

            if task.is_source_query:
                body_lines.append('context.load_query(source, conn=\'{}\')\n'.format(task.source_conn))
            else:
                body_lines.append('context.load(source, conn=\'{}\')\n'.format(task.source_conn))

        else:
            body_lines = get_function_body(task.execute_internal)
            body_lines = list(map(lambda x: x.replace('return ', ''), body_lines))
        source_lines = import_lines + ['\n\n'] + body_lines

        notebook = nbformat.v4.new_notebook()
        cell = nbformat.v4.new_code_cell(source=source_lines)
        notebook.cells.append(cell)

        ipynb_path = os.path.join(context.workdir, '.jupyter', 'notebook', task.name + '.ipynb')
        with open(ipynb_path, 'wb') as f:
            ipy_content = nbformat.writes(notebook)
            f.write(ipy_content.encode())
            f.flush()

        os.system('jupyter notebook {}.ipynb'.format(task.name))

    def short_desc(self):
        return 'debug a specified task in notebook'

    def config_parser(self, parser):
        parser.add_argument('task', help='the task to debug')
