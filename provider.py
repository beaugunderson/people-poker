import os
import re

from configobj import ConfigObj

def transform_module_name(string):
    """Converts from 'ThisStyle' to 'this-style'"""
    tokens = re.sub(r"(?<!^)([A-Z][a-z]|(?<=[a-z])[A-Z])", r" \1", string).split()

    return "-".join(tokens).lower()

class Provider(object):
    settings = {}

    def __init__(self, args=(), kwargs={}):
        super(Provider, self).__init__(*args, **kwargs)

        self.settings = {}

        self.load_settings()

    @property
    def name(self):
        return transform_module_name(self.__class__.__name__)

    def load_settings(self):
        print "Looking for %s in %s and %s.ini" % (self.name, 'config.ini', self.name)

        base = ConfigObj()

        for c in ["config.ini", "%s.ini" % self.name]:
            if not os.path.exists(c):
                continue

            parser = ConfigObj(c)

            if self.name in parser:
                base.merge(parser[self.name])

        self.settings = base
