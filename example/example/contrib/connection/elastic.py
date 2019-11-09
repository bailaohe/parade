# -*- coding:utf-8 -*-
from elasticsearch import Elasticsearch
from elasticsearch import helpers
import pandas as pd
from parade.connection import ConnConf, Connection


class ElasticConnection(Connection):
    def initialize(self, context, conf):
        Connection.initialize(self, context, conf)
        assert self.settings.host is not None, 'host of connection is required'
        assert self.settings.port is not None, 'port of connection is required'
        assert self.settings.db is not None, 'db of connection is required'
        assert self.settings.driver is not None and self.settings.driver == 'elastic', 'driver mismatch'

    def open(self):
        uri = self.settings.uri
        if uri is None:
            authen = None
            uripart = self.settings.host + ':' + str(self.settings.port) + '/' + self.settings.db
            if self.settings.user is not None:
                authen = self.settings.user
            if authen is not None and self.settings.password is not None:
                authen += ':' + self.settings.password
            if authen is not None:
                uripart = authen + '@' + uripart
            protocol = 'http'
            if self.settings.protocol is not None:
                protocol = self.settings.protocol
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
                    "_index": self.settings.db,
                    "_type": table,
                    "_id": record[df.index.name],
                    "_source": record
                } for record in records]
            else:
                actions = [{
                    "_index": self.settings.db,
                    "_type": table,
                    "_source": record
                } for record in records]

            if len(actions) > 0:
                helpers.bulk(es, actions)
