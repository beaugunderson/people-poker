import os
import re

from configobj import ConfigObj, flatten_errors
from validate import Validator


def transform_module_name(string):
    """Converts from 'ABCThisStyle' to 'abc-this-style'"""

    tokens = re.sub(r"(?<!^)([A-Z][a-z]|(?<=[a-z])[A-Z])",
            r" \1", string).split()

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
        print "Looking for %s in %s and %s.ini" % (self.name,
                'config.ini', self.name)

        base = ConfigObj()

        for c in ["config.ini", "%s.ini" % self.name]:
            if not os.path.exists(c):
                continue

            parser = ConfigObj(c, configspec='config-spec.ini')
            validator = Validator()

            results = parser.validate(validator)

            if results:
                if self.name in parser:
                    base.merge(parser[self.name])

                continue

            # Print an error message for sections with errors
            for section_list, key, _ in flatten_errors(parser, results):
                if key is not None:
                    print 'Failed to validate: "%s" section "%s"' % (key,
                            ', '.join(section_list))
                else:
                    print 'Section(s) missing: %s' % (', '.join(section_list))

        self.settings = base
