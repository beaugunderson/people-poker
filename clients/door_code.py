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


class EventHandler(pyinotify.ProcessEvent):
    def __init__(self, regex, door_settings, ldap_settings, position=0):
        super(pyinotify.ProcessEvent, self).__init__()

        self.regex = regex
        self.door_settings = door_settings
        self.ldap_settings = ldap_settings
        self.position = position

        context = zmq.Context()

        self.socket = context.socket(zmq.REQ)

    def process_IN_MODIFY(self, event):
        with open(event.pathname, "r") as f:
            f.seek(self.position)

            for line in f:
                match = self.regex.search(line)

                if match:
                    door_code = match.group('door_code')

                    id, name, guid = user_id_from_door_code(self.ldap_settings,
                            door_code)

                    self.socket.connect(self.door_settings["server_uri"])
                    self.socket.send_json({
                        'user_id': id,
                        'user_name': name,
                        'user_guid': guid,
                        'provider': 'door-code',
                        'time': dt.now().isoformat()
                    })

                    response = self.socket.recv_json()
                    self.socket.close()

                    print "Access granted to %s with code %s" \
                            % (name, door_code)

            self.position = f.tell()


def user_id_from_door_code(settings, door_code):
    query = "(&(objectCategory=person)(objectClass=user)(pinNumber=%s)" \
            "(!(userAccountControl:1.2.840.113556.1.4.803:=2))" \
            "(memberOf:1.2.840.113556.1.4.1941:=CN=Door Access,OU=" \
            "Security Groups,OU=MyBusiness,DC=synapsedev,DC=com))" % door_code

    # TODO Generalize this here and in ldap_provider.py
    l = ldap.initialize(settings['server_uri'])

    l.set_option(ldap.OPT_X_TLS_DEMAND, True)
    l.set_option(ldap.OPT_REFERRALS, 0)

    # Use hardcoded certificate file
    ldap.set_option(ldap.OPT_X_TLS_CACERTFILE,
            '/usr/local/spp/certificates/root-ca.crt')

    # For debugging information uncomment below
    l.set_option(ldap.OPT_DEBUG_LEVEL, 255)

    l.protocol_version = ldap.VERSION3

    l.simple_bind_s("%s\\%s" % (settings['ldap_root'],
        settings['username']),
        settings['password'])

    r = l.search_s(settings['ou_to_search'],
                   ldap.SCOPE_SUBTREE,
                   query,
                   ['cn', 'sAMAccountName', 'objectGUID'])

    l.unbind()

    # There should be no more and no less than one result per door code
    if not len(r) == 1:
        return None

    for dn, user in r:
        guid = ''.join(['%02X' % ord(c) for c in user['objectGUID'][0]])

        return (user['sAMAccountName'][0], user['cn'][0], guid)


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
