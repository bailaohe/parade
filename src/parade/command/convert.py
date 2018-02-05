import sys
import pandas as pd
from ..core.task import Task
from ..utils.log import parade_logger as logger

from . import ParadeCommand


class ConvertCommand(ParadeCommand):
    """
    The install command will install acontrib component into current workspace
    """

    requires_workspace = True

    def short_desc(self):
        return 'convert a source table to a target table'

    def config_parser(self, parser):
        parser.add_argument('-s', '--source', dest='source', help='the source table [conn_key:table_name]')
        parser.add_argument('-t', '--target', dest='target', help='set target table [conn_key:table_name]')

    def run_internal(self, context, **kwargs):
        source = kwargs.get('source')
        target = kwargs.get('target')

        if not sys.stdin.isatty() or not source:
            logger.info('use stdin as source')
            df = pd.read_json(sys.stdin, orient='records')
        else:
            if ':' not in source:
                logger.error('source should be in format [conn_key:table_name]')
                return Task.RET_CODE_FAIL
            else:
                (source_conn, source_table) = tuple(source.split(':'))
                df = context.get_connection(source_conn).load(source_table)

        if not sys.stdout.isatty() or not target:
            logger.info('use stdout as source')
            df.to_json(sys.stdout, orient='records')
        else:
            if ':' not in target:
                logger.error('target should be in format [conn_key:table_name]')
                return Task.RET_CODE_FAIL
            else:
                (target_conn, target_table) = tuple(target.split(':'))
                context.get_connection(target_conn).store(df, target_table)

        return Task.RET_CODE_SUCCESS

