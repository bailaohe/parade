from ..utils.log import logger


class Result(object):
    def __init__(self):
        self.data = None
        self.attributes = dict()

    @staticmethod
    def builder():
        return ResultBuilder()

    def content(self, labels=None):
        import pandas as pd
        if self.data is not None:
            if isinstance(self.data, pd.DataFrame):
                out_data = self.data

                nser_columns = list(out_data.select_dtypes(include=['datetime64']).keys())

                if len(nser_columns) > 0:
                    logger.warn(
                        "Detect columns {} with type that cannot be JSON serializable, which is automatically converted to string!".format(
                            list(nser_columns)))

                    for nser_column in nser_columns:
                        out_data[nser_column] = out_data[nser_column].apply(lambda x: str(x))

                if labels is not None and len(labels) > 0:
                    out_data = self.data.rename(columns=labels)
                return out_data.to_dict(orient='records')
        return self.data

    @property
    def attrs(self):
        return self.attributes

    def export(self, export_type, export_file='export', for_web=False, labels=None):
        """
        export to excel or csv
        :param export_type:
        :param export_file:
        :param for_web:
        :param labels:
        :return: the io content of the exported file
        """
        import pandas as pd
        if isinstance(self.data, pd.DataFrame):
            out_data = self.data
            if labels is not None and len(labels) > 0:
                out_data = self.data.rename(columns=labels)

            # Safe import for either Python 2.x or 3.x
            try:
                from io import BytesIO
            except ImportError:
                import StringIO as BytesIO
            io = BytesIO()

            if export_type == 'excel':
                writer = pd.ExcelWriter(io, engine='xlsxwriter') if for_web else pd.ExcelWriter(export_file,
                                                                                                engine='xlsxwriter')
                out_data.to_excel(writer, index=False)
                writer.save()
            elif export_type == 'csv':
                out_data.to_csv(io, index=False)
            else:
                raise NotImplementedError("export type {} is not supported".format(export_type))
            return io
        raise RuntimeError('the result cannot be exported')


class ResultBuilder(object):
    def __init__(self):
        self.result = Result()

    def set_data(self, data):
        self.result.data = data
        return self

    def set_attr(self, key, val):
        self.result.attributes[key] = val
        return self

    def set_attrs(self, attrs):
        if attrs is not None:
            self.result.attributes.update(attrs)
        return self

    def build(self):
        return self.result
