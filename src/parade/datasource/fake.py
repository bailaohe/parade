import pandas as pd

from ..datasource import Datasource


class FakeDatasource(Datasource):
    def store(self, df, table, db, **kwargs):
        print(df)

    def load_query(self, query, db, **kwargs):
        return pd.DataFrame()

    def load(self, table, db, **kwargs):
        return pd.DataFrame()

