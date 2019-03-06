class ValidParam:
    def __init__(self, param):
        self.param = param
        self.func = None
        self.default = False
        self.default_value = None
        self.process = None
        self.readable = None

    def fc(self, func):
        self.func = func
        return self

    def df(self, default_value=None):
        self.default = True
        self.default_value = default_value
        return self

    def p(self, process):
        self.process = process
        return self

    def r(self, readable):
        self.readable = readable
        return self
