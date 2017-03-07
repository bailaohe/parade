# -*- coding:utf-8 -*-
from parade.core.task import ETLTask


class ${TaskName}(ETLTask):

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
    def checkpoint_conn(self):
        """
        the connection to record the checkpoint
        default value is the target connection
        :return:
        """
        return self.target_conn

    @property
    def target_conn(self):
        """
        the target connection to write the result
        :return:
        """
        raise NotImplemented("The target is required")

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

    def execute_internal(self, context, **kwargs):
        """
        the internal execution process to be implemented
        :param context:
        :param kwargs:
        :return:
        """
        raise NotImplementedError

