class Plugin(object):

    def __init__(self):
        self.context = None
        self.conf = None

    def initialize(self, context, conf):
        self.context = context
        self.conf = conf
