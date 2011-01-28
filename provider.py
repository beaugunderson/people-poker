import os
import re

from configobj import ConfigObj

def transform_module_name(string):
    """Converts from 'ThisStyle' to 'this-style'"""
    tokens = re.sub(r"(?<!^)([A-Z][a-z]|(?<=[a-z])[A-Z])", r" \1", string).split()

    return "-".join(tokens).lower()

class Provider(object):
    settings = {}

    def __init__(self):
        self.settings = {}

        self.load_settings()

    def load_settings(self):
        me = transform_module_name(self.__class__.__name__)

        print "Looking for %s in %s and %s.ini" % (me, 'config.ini', me)

        base = ConfigObj()

        for c in ["config.ini", "%s.ini" % me]:
            if not os.path.exists(c):
                continue

            parser = ConfigObj(c)

            if me in parser:
                base.merge(parser[me])

        self.settings = base
