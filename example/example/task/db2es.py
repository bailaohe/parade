# -*- coding:utf-8 -*-
from parade.core.task import SqlETLTask


class Db2Es(SqlETLTask):

    @property
    def checkpoint_conn(self):
        """
        the connection to record the checkpoint
        default value is the target connection
        :return:
        """
        return 'rdb-conn'

    @property
    def target_conn(self):
        """
        the target connection to write the result
        :return:
        """
        return 'elastic-conn'

    @property
    def target_table(self):
        """
        the target table to store the result
        :return:
        """
        return 'delivery_history'

    @property
    def etl_sql(self):
        return """
        select
        "ID",
        "Project Code",
        "PQ #",
        "PO / SO #",
        "ASN/DN #",
        "Country",
        "Managed By",
        "Fulfill Via",
        "Vendor INCO Term",
        "Shipment Mode",
        "PQ First Sent to Client Date",
        "PO Sent to Vendor Date",
        "Scheduled Delivery Date",
        "Delivered to Client Date",
        "Delivery Recorded Date",
        "Product Group",
        "Sub Classification",
        "Vendor" ,
        "Item Description",
        "Molecule/Test Type",
        "Brand",
        "Dosage",
        "Dosage Form",
        "Unit of Measure Per Pack",
        "Line Item Quantity",
        "Line Item Value",
        "Pack Price",
        "Unit Price",
        "Manufacturing Site",
        "First Line Designation",
        "Weight in Kilograms",
        "Freight Cost in USD",
        COALESCE("Line Item Insurance in USD", 0.0) as "Line Item Insurance in USD"
        from delivery_history
        """

    @property
    def source_conn(self):
        return 'rdb-conn'

    @property
    def deps(self):
        return ["csv2db"]
