# -*- coding:utf-8 -*-
from elasticsearch import Elasticsearch
from elasticsearch import helpers
import pandas as pd
from parade.datasource import Datasource, Connection


class ElasticDatasource(Datasource):
    def initialize(self, context, conf, key):
        Connection.initialize(self, context, conf, key)
        assert self.host is not None, 'host of datasource is required'
        assert self.port is not None, 'port of datasource is required'
        assert self.driver is not None and self.driver == 'elastic', 'driver mismatch'

    def open(self, db):
        uri = self.uri
        if uri is None:
            authen = None
            uripart = self.host + ':' + str(self.port) + '/' + str(db or self.default_db)
            if self.user is not None:
                authen = self.user
            if authen is not None and self.password is not None:
                authen += ':' + self.password
            if authen is not None:
                uripart = authen + '@' + uripart
            protocol = 'http'
            if self.protocol is not None:
                protocol = self.protocol
            uri = protocol + '://' + uripart

        return Elasticsearch(uri)

    def load(self, table, **kwargs):
        raise NotImplementedError

    def load_query(self, query, **kwargs):
        raise NotImplementedError

    def store(self, df, table, **kwargs):
        if isinstance(df, pd.DataFrame):
            es = self.open()

            records = df.to_dict(orient='records')

            if df.index.name:
                actions = [{
                    "_index": self.db,
                    "_type": table,
                    "_id": record[df.index.name],
                    "_source": record
                } for record in records]
            else:
                actions = [{
                    "_index": self.db,
                    "_type": table,
                    "_source": record
                } for record in records]

            if len(actions) > 0:
                helpers.bulk(es, actions)
