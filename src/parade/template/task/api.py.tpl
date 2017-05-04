# -*- coding:utf-8 -*-
from parade.core.task import APITask


class ${TaskName}(APITask):

    def execute_internal(self, context, **kwargs):
        raise NotImplementedError

    @property
    def labels(self):
        return {}

    @property
    def export_labels(self):
        return {}

