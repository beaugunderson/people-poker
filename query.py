#!/usr/bin/env python2.7

import json
import os
import sys

from configobj import ConfigObj

# XXX
sys.path.append(os.path.abspath('..'))

from spp.models import ModelEncoder, User
from spp.utilities import create_db_session


def query_user_status(account):
    """ Returns JSON output for the current statuses of an account """

    parser = ConfigObj('config.ini')

    session = create_db_session(parser["database"])

    try:
        user = session.query(User).filter(
                User.account == account).one()

        return json.dumps(user.statuses, cls=ModelEncoder, indent=4)
    except:
        raise

if __name__ == "__main__":
    print query_user_status("beau")
