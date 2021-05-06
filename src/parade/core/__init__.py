class Plugin(object):

    def __init__(self):
        self.context = None
        self.conf = None
        self.key = None

    def initialize(self, context, conf, key):
        self.context = context
        self.conf = conf
        self.key = key
