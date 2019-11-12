import sys
import pandas as pd
from ..core.task import Task
from ..utils.log import parade_logger as logger

from . import ParadeCommand


class ConvertCommand(ParadeCommand):
    """
    The install command will install acontrib component into current workspace
    """

    requires_workspace = False

    def short_desc(self):
        return 'convert a source table to a target table'

    def config_parser(self, parser):
        parser.add_argument('--source-conn', dest='source-conn', help='the source connection to extract data, formatted'
                                                                      'in conn_key or ds_key/db_name')
        parser.add_argument('--source-table', dest='source-table', help='the source table to extract data, formatted in'
                                                                        'conn_key:table_name'
                                                                        'or ds_key/db_name:table_name')
        parser.add_argument('--target-table', dest='target-table', help='set target table to write data, formatted in'
                                                                        'conn_key:table_name'
                                                                        'or ds_key/db_name:table_name')
        parser.add_argument('--target-file', dest='target-file', help='set the target file path to dump data')

    def run_internal(self, context, **kwargs):
        source_conn = kwargs.get('source-conn')
        source_table = kwargs.get('source-table')
        target_table = kwargs.get('target-table')
        target_file = kwargs.get('target-file')

        # if not sys.stdin.isatty() or (not source_conn and not source_table):
        if sys.stdin.isatty() or (not source_conn and not source_table):
            logger.info('use stdin as source')
            df = pd.read_json(sys.stdin, orient='records')
        elif source_conn:
            df = pd.read_json(sys.stdin, orient='records')
            pass
        else:
            if ':' not in source_table:
                logger.error('source should be in format [conn_key:table_name]')
                return Task.RET_CODE_FAIL
            else:
                (source_conn, table_name) = tuple(source_table.split(':'))
                df = context.get_connection(source_conn).load(table_name)

        # if not sys.stdout.isatty() or not target_table:
        if sys.stdout.isatty() or not target_table:
            logger.info('use stdout as source')
            df.to_json(sys.stdout, orient='records')
        else:
            if ':' not in target_table:
                logger.error('target should be in format [conn_key:table_name]')
                return Task.RET_CODE_FAIL
            else:
                (target_conn, table_name) = tuple(target_table.split(':'))
                context.get_connection(target_conn).store(df, table_name)

        return Task.RET_CODE_SUCCESS

