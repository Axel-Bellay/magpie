class Command:

    def __init__(self, name):
        self.name = name
        self.performed = False
        self.cmd = None
        self.timeout = None
        self.lengthout = None