# -*- coding:utf-8 -*-

import datetime
import os
from io import BytesIO

import pandas as pd
from pandas.compat import cPickle as pkl

from ..connection import Connection


class LocalFile(Connection):
    @staticmethod
    def export(df, table, export_type='excel', target_path=None, if_exists='replace', suffix=None):
        if target_path:
            if export_type == 'excel' and not suffix:
                suffix = 'xlsx'
            target_file = os.path.join(target_path,
                                       table + '-' + str(datetime.date.today())) + '.' + str(suffix or export_type)
            if if_exists == 'replace' and os.path.exists(target_file):
                os.remove(target_file)
            export_io = target_file

        else:
            export_io = BytesIO()

        if export_type == 'excel':
            writer = pd.ExcelWriter(export_io, engine='xlsxwriter')
            df.to_excel(writer, index=False)
            writer.save()
        elif export_type == 'csv':
            if not target_path:
                export_io = BytesIO(df.to_csv(None, index=False, chunksize=4096).encode())
            else:
                df.to_csv(os.path.join(target_path, table), index=False, chunksize=4096)
        elif export_type == 'json':
            if not target_path:
                export_io = BytesIO(df.to_json(None, orient='records', force_ascii=False).encode())
            else:
                df.to_json(os.path.join(target_path, table), orient='records', force_ascii=False)
        elif export_type == 'pickle':
            pkl.dump(df, export_io, protocol=pkl.HIGHEST_PROTOCOL)
        else:
            raise NotImplementedError("export type {} is not supported".format(export_type))
        return export_io, table + '.' + str(suffix or export_type)

    def store(self, df, table, **kwargs):
        target_path = self.datasource.db if self.datasource.db else '.'
        export_type = self.datasource.protocol if self.datasource.protocol else 'json'
        if_exists = kwargs.get('if_exists', 'replace')

        os.makedirs(target_path, exist_ok=True)
        LocalFile.export(df, table, export_type=export_type, target_path=target_path, if_exists=if_exists)

    def load_query(self, query, **kwargs):
        raise NotImplementedError

    def load(self, table, **kwargs):
        raise NotImplementedError
