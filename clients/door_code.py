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
    def __init__(self, position=0):
        super(pyinotify.ProcessEvent, self).__init__()

        context = zmq.Context()

        self.config = ConfigObj("door-code.ini")
        self.socket = context.socket(zmq.REQ)
        self.position = position

    def process_IN_MODIFY(self, event):
        with open(event.pathname, "r") as f:
            f.seek(self.position)

            for line in f:
                match = door_code.search(line)

                if match:
                    self.socket.connect(self.config["door-code-client"]["server_uri"])
                    self.socket.send_json({
                        'user_id': match.group('door_code'),
                        'provider': 'door-code',
                        'time': dt.now()
                    })

                    response = self.socket.recv_json()
                    self.socket.close()

                    print "Access granted to this user's code: %s" % match.group('door_code')

            self.position = f.tell()

@plac.annotations(
    path=("Path to the log file to watch for door codes", 'option', 'p'))

def main(path):
    if not path:
        print "You must provide a path to watch."
        sys.exit(0)

    door_code = re.compile(r"Access granted to '(?P<door_code>\d+)'$")

    position = os.path.getsize(path)

    wm = pyinotify.WatchManager()

    notifier = pyinotify.AsyncNotifier(wm, EventHandler(position))

    wm.add_watch(path, pyinotify.IN_MODIFY, rec=True)

    try:
        asyncore.loop()
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    plac.call(main)
