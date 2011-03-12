#!/usr/bin/env python2.7

import bottle
import json
import os
import sys

sys.path.append(os.path.abspath('..'))

from bottle import route, run, request, response, abort
from datetime import datetime as dt
from configobj import ConfigObj
from sqlalchemy import and_
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound

from spp.models import ModelEncoder, Status, User
from spp.utilities import create_db_session

parser = ConfigObj('config.ini')

# Initialize the database connection
session = create_db_session(parser["database"])

def json_or_jsonp(o, request, response):
    output = json.dumps(o, cls=ModelEncoder)

    if 'callback' in request.GET:
        response.set_content_type('text/javascript')

        output = "%s(%s)" % (request.GET['callback'], output)
    else:
        response.set_content_type('application/json')

    return output

# Get a list of users
@route('/user', method='GET')
def get_user_index():
    users = session.query(User).all()

    return json_or_jsonp(users, request, response)

# Get a user
@route('/user/:username', method='GET')
def get_user(username):
    # TODO differentiate between a username and an ID
    user = session.query(User).join(Status).filter(
            User.account == username).one()

    return json_or_jsonp(user, request, response)

# Get a list of status updates
@route('/status', method='GET')
def get_status_index():
    status = session.query(Status).all()

    return json_or_jsonp(status, request, response)

# Get a user's status
@route('/status/:username', method='GET')
def get_status(username):
    # TODO differentiate between a username and an ID
    status = session.query(Status).join(User).filter(
            User.account == username).all()

    return json_or_jsonp(status, request, response)

# Update a user's status
@route('/status/:username/:status_type', method=['POST', 'PUT'])
def set_status(username, status_type):
    try:
        user = session.query(User).filter(
            User.account == username).one()
    except MultipleResultsFound:
        raise
    except NoResultFound:
        raise

    try:
        status = session.query(Status).filter(and_(
            Status.user == user,
            Status.provider == 'web-update')).one()

        status.status = status_type
        status.update_time = dt.now()

        session.merge(status)
        session.commit()
    except MultipleResultsFound:
        raise
    except NoResultFound:
        status = Status('web-update', status_type, dt.now())

        status.user = user

        session.add(status)
        session.commit()

bottle.debug(True)

application = bottle.app()
#run(host='0.0.0.0', port=8000)
