# -*- coding:utf-8 -*-
from parade.core.task import SingleSourceETLTask


class ${TaskName}(SingleSourceETLTask):
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

    @property
    def source_conn(self):
        """
        the source connection to write the result
        :return:
        """
        raise NotImplementedError("The source connection is required")

    @property
    def source(self):
        """
        the single source (table/query) to process etl
        :return:
        """
        raise NotImplementedError("The source is required")

    @property
    def is_source_query(self):
        """
        whether the source is query or not (table)
        :return:
        """
        return True

    def transform(self, df):
        """
        process to transform the source dataframe to another one
        :return:
        """
        return df
