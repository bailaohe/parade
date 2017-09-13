# -*- coding:utf-8 -*-
from parade.core.task import SqlETLTask


class ${TaskName}(SqlETLTask):

    @property
    def checkpoint_round(self):
        """
        the time interval the checkpoint will align to
        default value is 1 day
        :return:
        """
        return 3600 * 24

    @property
    def checkpoint_timezone(self):
        """
        the timezone used when recording checkpoint
        default: None, use the local timezone
        :return:
        """
        return None

    @property
    def checkpoint_column(self):
        """
        the column to use as the clue for checkpoint
        :return:
        """
        if self.target_mode == 'append':
            raise NotImplementedError
        return None

    @property
    def target_conn(self):
        """
        the target connection to write the result
        :return:
        """
        raise NotImplementedError("The target is required")

    @property
    def target_table(self):
        """
        the target table to store the result
        :return:
        """
        return self.name

    @property
    def target_mode(self):
        """
        what to do if the target table exists, replace / append / fail
        :return:
        """
        return 'replace'

    @property
    def target_typehints(self):
        """
        a dict of column_name => datatype, to customize the data type before write target
        :return:
        """
        return {}

    @property
    def source_conn(self):
        """
        the source connection to write the result
        :return:
        """
        raise NotImplementedError("The source is required")

    @property
    def etl_sql(self):
        """
        the single sql statement to process etl
        :return:
        """
        raise NotImplementedError("The etl-sql is required")

