# -*- coding:utf-8 -*-
from parade.core.task import ETLTask
import pandas as pd


class Csv2Db(ETLTask):
    @property
    def target_table(self):
        """
        the target table to store the result
        :return:
        """
        return 'delivery_history'

    @property
    def target_conn(self):
        """
        the target connection to write the result
        :return:
        """
        return 'rdb-conn'

    def execute_internal(self, context, **kwargs):
        """
        the internal execution process to be implemented
        :param context:
        :param kwargs:
        :return:
        """
        df = pd.read_csv('http://www.usaid.gov/opengov/developer/datasets/SCMS_Delivery_History_Dataset_20150929.csv')
        df = df.rename(columns={'Unit of Measure (Per Pack)': 'Unit of Measure Per Pack',
                                'Weight (Kilograms)': 'Weight in Kilograms',
                                'Freight Cost (USD)': 'Freight Cost in USD',
                                'Line Item Insurance (USD)': 'Line Item Insurance in USD'})
        return df

