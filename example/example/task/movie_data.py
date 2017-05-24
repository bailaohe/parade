# -*- coding:utf-8 -*-

from parade.core.task import ETLTask
from parade.type import stdtypes
import pandas as pd


class MovieData(ETLTask):

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
            'movie_title': stdtypes.StringType(128),
            'genres': stdtypes.StringType(128),
            'genres_root': stdtypes.StringType(32),
            'content_rating': stdtypes.StringType(16),
            'title_year': stdtypes.IntegerType(),
            'budget': stdtypes.IntegerType(20),
        }

    @property
    def target_indexes(self):
        """
        a string or a string-tuple or a string/string-tuple list to specify the indexes on the target table
        :return:
        """
        return ['movie_title', ('title_year', 'genres')]

    def execute_internal(self, context, **kwargs):
        """
        the internal execution process to be implemented
        :param context:
        :param kwargs:
        :return:
        """
        df = pd.read_csv('https://raw.githubusercontent.com/bailaohe/parade/master/assets/movie_metadata.csv')

        # Process projection on the dataset to get our interested attributes
        df = df[['movie_title', 'genres', 'title_year', 'content_rating', 'budget', 'num_voted_users', 'imdb_score']]

        # Filter out records with *NAN* title_year and budget
        df = df[pd.notnull(df['title_year'])]
        df = df[df['budget'] > 0]

        # Extract the genres ROOT
        df['genres_root'] = df['genres'].apply(lambda g: g.split('|')[0])

        return df

