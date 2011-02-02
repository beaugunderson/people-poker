#!/usr/bin/env python2.7

import json
import os
import sqlalchemy
import sys

from configobj import ConfigObj

# XXX
sys.path.append(os.path.abspath('..'))

from spp.models import User
from spp.utilities import create_db_session


def query_user_status(user_id):
    """ Returns JSON output for the current statuses of a given user_id """

    parser = ConfigObj('config.ini')

    session = create_db_session(parser["database"])

    try:
        user = session.query(User).filter(User.user_id == user_id).one()

        import pprint

        return pprint.pformat(user.statuses)

        #return json.dumps(user.statuses)
    except:
        raise

if __name__ == "__main__":
    print query_user_status("beau")
