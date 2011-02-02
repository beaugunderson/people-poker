#!/usr/bin/env python2.7

import asyncore
import ldap
import os
import plac
import pyinotify
import re
import sys
import zmq

from configobj import ConfigObj
from datetime import datetime as dt

# XXX
sys.path.append(os.path.abspath('../..'))

from spp.utilities import connect_and_search_ldap


class EventHandler(pyinotify.ProcessEvent):
    def __init__(self, regex, door_settings, ldap_settings, position=0):
        super(pyinotify.ProcessEvent, self).__init__()

        self.regex = regex
        self.door_settings = door_settings
        self.ldap_settings = ldap_settings
        self.position = position

        self.context = zmq.Context()

    def process_IN_MODIFY(self, event):
        with open(event.pathname, "r") as f:
            f.seek(self.position)

            for line in f:
                match = self.regex.search(line)

                if match:
                    door_code = match.group('door_code')

                    id, guid, name = user_id_from_door_code(self.ldap_settings,
                            door_code)

                    print "Access granted to %s with code %s" \
                            % (name, door_code)

                    socket = self.context.socket(zmq.REQ)

                    socket.connect(self.door_settings["server_uri"])
                    socket.send_json({
                        'user_id': id,
                        'user_guid': guid,
                        'user_name': name,
                        'status': 'in',
                        'provider': 'door-code',
                        'time': dt.now().isoformat()
                    })

                    response = socket.recv_json()

                    socket.close()

            self.position = f.tell()


def user_id_from_door_code(settings, door_code):
    query = "(&(objectCategory=person)(objectClass=user)(pinNumber=%s)" \
            "(!(userAccountControl:1.2.840.113556.1.4.803:=2))" \
            "(memberOf:1.2.840.113556.1.4.1941:=CN=Door Access,OU=" \
            "Security Groups,OU=MyBusiness,DC=synapsedev,DC=com))" % door_code

    # TODO Generalize this here and in ldap_provider.py
    r = connect_and_search_ldap(settings, settings['ou_to_search'], query,
                   ['cn', 'sAMAccountName', 'objectGUID'])

    # There should be no more and no less than one result per door code
    if not len(r) == 1:
        return None

    for dn, user in r:
        guid = ''.join(['%02X' % ord(c) for c in user['objectGUID'][0]])

        return (user['sAMAccountName'][0], guid, user['cn'][0])


@plac.annotations(
    path=("Path to the log file to watch for door codes", 'option', 'p'))
def main(path):
    if not path:
        print "You must provide a path to watch."
        sys.exit(0)

    door_code = re.compile(r"Access granted to '(?P<door_code>\d+)'$")
    settings = ConfigObj("door-code.ini")

    position = os.path.getsize(path)

    wm = pyinotify.WatchManager()

    notifier = pyinotify.AsyncNotifier(wm, EventHandler(door_code,
        settings['door-code'], settings['ldap'], position))

    wm.add_watch(path, pyinotify.IN_MODIFY, rec=True)

    try:
        asyncore.loop()
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    plac.call(main)
