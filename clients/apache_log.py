#!/usr/bin/env python2.7

import asyncore
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


class EventHandler(pyinotify.ProcessEvent):
    def __init__(self, regex, settings, position=0):
        super(pyinotify.ProcessEvent, self).__init__()

        self.regex = regex
        self.settings = settings
        self.position = position

        self.context = zmq.Context()

    def process_IN_MODIFY(self, event):
        with open(event.pathname, "r") as f:
            f.seek(self.position)

            for line in f:
                #print "DEBUG: Got line %s" % line

                match = self.regex.search(line)

                if match:
                    username = match.group('username')

                    if username == "-":
                        continue

                    print "DEBUG: Got username %s" %username

                    if re.search(r"\\", username):
                        username = re.sub(r".*\\", "", username)

                    username = username.lower()

                    print "DEBUG: Mogrified to %s" %username

                    socket = self.context.socket(zmq.REQ)

                    socket.connect(self.settings["server_uri"])
                    socket.send_json({
                        'account': username,
                        'status': 'in',
                        'provider': 'apache-log',
                        'time': dt.now().isoformat()
                    })

                    response = socket.recv_json()

                    socket.close()

            self.position = f.tell()


@plac.annotations(
    path=("Path to the log file to watch for Apache visitiors", 'option', 'p'))
def main(path):
    if not path:
        path = "/var/log/apache2/intranet.access.log"

        print "Using default path of %s." % path

    username = re.compile(r"[^ ]+ - (?P<username>[^ ]+) \[")
    settings = ConfigObj("apache-log.ini")

    position = os.path.getsize(path)

    wm = pyinotify.WatchManager()

    pyinotify.AsyncNotifier(wm, EventHandler(username,
        settings['apache-log'], position))

    wm.add_watch(path, pyinotify.IN_MODIFY, rec=True)

    try:
        asyncore.loop()
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    plac.call(main)