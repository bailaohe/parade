# -*- coding:utf-8 -*-
from parade.core.task import SingleSourceETLTask
from parade.type import stdtypes


class GenresDistrib(SingleSourceETLTask):

    @property
    def target_conn(self):
        """
        the target connection to write the result
        :return:
        """
        return 'rdb-conn'

    @property
    def target_typehints(self):
        """
        a dict of column_name => datatype, to customize the data type before write target
        :return:
        """
        return {
            'genres_root': stdtypes.StringType(32),
            'avg_budget': stdtypes.IntegerType(20),
            'total_count': stdtypes.IntegerType(),
            'excellence_count': stdtypes.IntegerType(),
        }

    @property
    def source_conn(self):
        """
        the source connection to write the result
        :return:
        """
        return 'rdb-conn'

    @property
    def source(self):
        """
        the single sql statement to process etl
        :return:
        """
        return """
        SELECT
          genres_root,
          COUNT(1) DIV 1                            total_count,
          SUM(IF(imdb_score >= 7, 1, 0)) DIV 1      excellence_count,
          SUM(IF(imdb_score >= 7, 1, 0)) / count(1) excellence_rate,
          AVG(budget) DIV 1                         avg_budget
        FROM movie_data
        GROUP BY genres_root
        ORDER BY excellence_count DESC;
        """

    @property
    def deps(self):
        """
        a string-array to specified the dependant tasks has to be completed before this one
        :return:
        """
        return ['movie_data']
