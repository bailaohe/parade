from parade.connection import Connection
import pandas as pd
import os
import datetime


class LocalFile(Connection):
    def store(self, df, table, **kwargs):
        target_path = self.datasource.db if self.datasource.db else '.'
        export_type = self.datasource.protocol if self.datasource.protocol else 'json'
        if_exists = kwargs.get('if_exists', 'replace')

        os.makedirs(target_path, exist_ok=True)

        if export_type == 'excel':
            target_file = os.path.join(target_path, table + '-' + str(datetime.date.today())) + '.xlsx'
            if if_exists == 'replace' and os.path.exists(target_file):
                os.remove(target_file)
            writer = pd.ExcelWriter(target_file, engine='xlsxwriter')
            df.to_excel(writer, index=False)
            writer.save()
        elif export_type == 'csv':
            target_file = os.path.join(target_path, table + '-' + str(datetime.date.today())) + '.csv'
            if if_exists == 'replace' and os.path.exists(target_file):
                os.remove(target_file)
            df.to_csv(target_file, index=False, chunksize=4096)
        elif export_type == 'json':
            target_file = os.path.join(target_path, table + '-' + str(datetime.date.today())) + '.json'
            if if_exists == 'replace' and os.path.exists(target_file):
                os.remove(target_file)
            df.to_json(target_file, orient='records')
        elif export_type == 'pickle':
            target_file = os.path.join(target_path, table + '-' + str(datetime.date.today())) + '.dat'
            if if_exists == 'replace' and os.path.exists(target_file):
                os.remove(target_file)
            df.to_pickle(target_file)
        else:
            raise NotImplementedError("export type {} is not supported".format(export_type))

    def load_query(self, query, **kwargs):
        raise NotImplementedError

    def load(self, table, **kwargs):
        raise NotImplementedError
