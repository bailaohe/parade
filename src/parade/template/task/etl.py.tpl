# -*- coding:utf-8 -*-
from parade.core.task import ETLTask


class ${TaskName}(ETLTask):
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
    def target_pkey(self):
        """
        a string or a string-tuple to specify the primary key on the target table
        :return:
        """
        return None

    @property
    def target_indexes(self):
        """
        a string or a string-tuple or a string/string-tuple list to specify the indexes on the target table
        :return:
        """
        """
        :return:
        """
        return []

    @property
    def target_checkpoint_column(self):
        """
        the columns to use as the clue of last/checkpoint in target table
        :return:
        """
        return None

    def execute_internal(self, context, **kwargs):
        """
        the internal execution process to be implemented
        :param context:
        :param kwargs:
        :return:
        """
        raise NotImplementedError
