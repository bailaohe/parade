# -*- coding:utf-8 -*-
from parade.core.task import SingleSourceETLTask


class Db2Es(SingleSourceETLTask):

    @property
    def target_conn(self):
        """
        the target connection to write the result
        :return:
        """
        return 'elastic-conn'

    @property
    def source(self):
        return """
        SELECT
            movie_title, genres,
            title_year, content_rating,
            budget, num_voted_users, imdb_score
        FROM movie_data
        """

    @property
    def source_conn(self):
        return 'rdb-conn'

    @property
    def deps(self):
        return ["movie_data"]
