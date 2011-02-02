import logging
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
    def __init__(self, args=(), kwargs={}):
        super(Provider, self).__init__(*args, **kwargs)

        self.logger = logging.getLogger()

        self.load_settings()

    def __str__(self):
        return transform_module_name(self.__class__.__name__)

    def poll(self):
        pass

    def load_settings(self):
        self.logger.info("Looking for %s in %s, %s.ini" % (self,
                'config.ini', self))

        base = ConfigObj()

        for c in ["config.ini", "%s.ini" % self]:
            if not os.path.exists(c):
                continue

            parser = ConfigObj(c, configspec='config-spec.ini')
            validator = Validator()

            results = parser.validate(validator)

            if results:
                if str(self) in parser:
                    base.merge(parser[str(self)])

                continue

            # Print an error message for sections with errors
            for section_list, key, _ in flatten_errors(parser, results):
                if key is not None:
                    self.logger.error('Failed to validate: "%s" section "%s"' \
                            % (key, ', '.join(section_list)))
                else:
                    self.logger.error('Section(s) missing: %s' \
                            % (', '.join(section_list)))

        self.settings = base
