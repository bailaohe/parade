from ..connection import Connection
import pandas as pd


class FakeConnection(Connection):
    def store(self, df, table, **kwargs):
        print(df)

    def load_query(self, query, **kwargs):
        return pd.DataFrame()

    def load(self, table, **kwargs):
        return pd.DataFrame()

