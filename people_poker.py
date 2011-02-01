#!/usr/bin/env python2.7

import daemon
import imp
import os
import pkgutil
import sys
import time
import threading

from collections import defaultdict
from datetime import datetime as dt

from sqlalchemy import create_engine, ForeignKey, and_
from sqlalchemy.orm import backref, relationship, sessionmaker

from models import Base, User, Device, Status

from provider import Provider


class PeoplePoker(object):
    threads = []

    def __init__(self):
        super(PeoplePoker, self).__init__()

        # Get all of the provider classes and instantiate them
        self.providers = self.get_providers()
        self.provider_instances = self.get_provider_instances()

        # Initialize the database connection
        engine = create_engine('sqlite:///:memory:', echo=False)

        Base.metadata.create_all(engine)

        Session = sessionmaker()
        Session.configure(bind=engine)

        self.session = Session()

        # Start any server providers (like the ZMQ server provider)
        for provider in self.provider_instances['server']:
            print "Starting server for %s" % provider.name

            self.threads.append(provider)

        for thread in self.threads:
            thread.start()

    def get_provider_instances(self):
        """Instantiate collected providers."""

        provider_instances = defaultdict(list)

        for type in self.providers.keys():
            for provider in self.providers[type]:
                provider_instances[type].append(provider())

        return provider_instances

    def get_providers(self):
        """Collect all providers and classify them by what they provide."""

        provider_path = [os.path.join(sys.path[0], 'providers')]

        for loader, name, ispkg in pkgutil.iter_modules(provider_path):
            file, pathname, desc = imp.find_module(name, provider_path)

            imp.load_module(name, file, pathname, desc)

        subclasses = Provider.__subclasses__()

        providers = defaultdict(list)

        for subclass in subclasses:
            print "Subclass %s provides %s" % (subclass, subclass.provides)

            for type in subclass.provides:
                providers[type].append(subclass)

        return providers

    def update_status(self, user, provider, status, time):
        if not isinstance(time, dt):
            time = dt.strptime(time, '%Y-%m-%dT%H:%M:%S.%f')

        try:
            status = self.session.query(Status).filter(_and(
                Status.user == user,
                Status.provider == provider)).one()

            status.provider = provider
            status.status = status
            status.update_time = time

            self.session.commit()
        except:
            status = Status(provider, status, time)

            self.session.add(status)
            self.session.commit()

    def query_providers(self):
        """Query the various providers."""

        # Update data from all providers
        for type in ['status', 'devices', 'users']:
            for provider in self.provider_instances[type]:
                print "Polling provider: %s" % provider

                # Call the polling function of the provider to
                # refresh the data
                try:
                    provider.poll()
                except Exception as e:
                    print "There was an error polling %s: %s" % (provider, e)

        # Update data from status providers
        for provider in self.provider_instances['status']:
            for update in provider.updates:
                print "Got update: %s" % update

        # Update data from device providers
        devices = defaultdict(list)

        for provider in self.provider_instances['devices']:
            for device in provider.devices:
                devices[device].append(provider.name)

        # Iterate through each user
        for user in self.session.query(User):
            print "Found user: %s" % user

            # Iterate through all the user's devices and see
            # if any of them are active
            for device in user.devices:
                print "User has device: %s" % device

                if device.mac_address in devices:
                    for provider in devices[device.mac_address]:
                        self.update_status(provider, 'in', dt.now())
                else:
                    for provider in devices[device.mac_address]:
                        self.update_status(provider, 'out', dt.now())

    def loop(self):
        """The main program loop."""

        while True:
            self.query_providers()

            time.sleep(10)

    def run_as_daemon(self):
        """Run people poker as a daemon process."""

        print "Starting People Poker daemon"

        logs = os.path.join(os.getcwd(), "logs")

        try:
            os.mkdir(logs)
        except:
            pass

        error_log = open(os.path.join(logs, 'error.log'), 'w+')
        output_log = open(os.path.join(logs, 'output.log'), 'w+')

        with daemon.DaemonContext(stdout=output_log,
                                  stderr=error_log,
                                  working_directory=os.getcwd()):
            self.loop()

        # Stop any running threads
        for thread in self.threads():
            thread.stop()

        # Clean up any open files.
        error_log.close()
        output_log.close()

if __name__ == "__main__":
    # XXX Is this a hack?
    sys.path.append(os.path.abspath('..'))

    pp = PeoplePoker()

    try:
        pp.loop()
    finally:
        for thread in pp.threads:
            print "Attempting to stop thread %s" % thread

            thread.stop()

    sys.exit()
