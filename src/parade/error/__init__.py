FLOW_NOT_FOUND = (100, 404, 'flow [{flow}] not found')

class ParadeError(RuntimeError):
    """
    base exception of parade
    """

    code = 0
    status = 200
    message = 'OK'
    args = {}

    def __init__(self, **err_args):
        self.args = err_args

    @property
    def reason(self):
        return self.message.format(**self.args)
