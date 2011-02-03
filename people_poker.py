#!/usr/bin/env python2.7

import daemon
import imp
import itertools
import logging
import os
import plac
import pkgutil
import sys
import time
import threading

# XXX For debugging
#from IPython.Shell import IPShellEmbed; ipshell = IPShellEmbed()

from collections import defaultdict
from configobj import ConfigObj
from datetime import datetime as dt
from pprint import pformat
from sqlalchemy import and_

# XXX Is this a hack? If not, where's a better place for it?
sys.path.append(os.path.abspath('..'))

from spp.models import Base, User, Device, Status
from spp.provider import Provider

from spp.utilities import create_db_session


class PeoplePoker(object):
    threads = []

    def __init__(self, configuration=""):
        super(PeoplePoker, self).__init__()

        # TODO Push logging setup into a config file
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.DEBUG)

        formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')

        console_handler = logging.StreamHandler()

        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(formatter)

        self.logger.addHandler(console_handler)

        self.logger.info("Starting up at %s..." % dt.now())

        # Get all of the provider classes and instantiate them
        self.providers = self.get_providers()
        self.provider_instances = self.get_provider_instances()

        self.logger.info("Providers: " + pformat([(type, \
                [provider.__name__ for provider in providers]) \
                for type, providers in self.providers.iteritems()]))

        self.logger.info("Instances: " + pformat([(type, \
                [provider.__class__.__name__ for provider in providers]) \
                for type, providers in self.provider_instances.iteritems()]))

        parser = ConfigObj('config.ini')

        # Initialize the database connection
        self.session = create_db_session(parser["database%s" % configuration])

        # Start any server providers (like the ZMQ server provider)
        for provider in self.provider_instances['server']:
            self.logger.info("Starting server for %s" % provider)

            self.threads.append(provider)

        for thread in self.threads:
            thread.start()

    def get_provider_instances(self):
        """
        Instantiate collected providers, taking care to only instantiate each
        provider class once.
        """

        # Get a list of provider classes without duplicates
        providers = list(set(itertools.chain(*self.providers.values())))

        provider_instances = defaultdict(list)

        for provider in providers:
            instance = provider()

            for type, classes in self.providers.iteritems():
                for provider_class in classes:
                    if isinstance(instance, provider_class):
                        provider_instances[type].append(instance)

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
            self.logger.info("Found provider %s providing %s" \
                    % (subclass.__name__, ', '.join(subclass.provides)))

            for type in subclass.provides:
                providers[type].append(subclass)

        return providers

    def update_status(self, user, provider, status, time):
        if not isinstance(time, dt):
            time = dt.strptime(time, '%Y-%m-%dT%H:%M:%S.%f')

        self.logger.debug("Time: %s" % time)

        try:
            status = self.session.query(Status).filter(and_(
                Status.user == user,
                Status.provider == provider)).one()

            status.provider = provider
            status.status = status
            status.update_time = time

            self.session.merge(status)
            self.session.commit()
        except Exception as e:
            self.logger.exception(e)

            status = Status(provider, status, time)

            status.user = user

            self.session.add(status)
            self.session.commit()

    def query_providers(self):
        """Query the various providers."""

        # Poll data for all providers
        for type in ['status', 'devices', 'users']:
            for provider in self.provider_instances[type]:
                self.logger.info("Polling provider %s" % provider)

                # Call the polling function of the provider to
                # refresh the data
                try:
                    provider.poll()
                except Exception as e:
                    self.logger.error("There was an error polling %s" \
                            % provider)

                    self.logger.exception(e)

        # Update data from user providers
        for provider in self.provider_instances['users']:
            self.logger.debug("Got users: %s" % pformat(provider.users))

            for user in provider.users:
                try:
                    db_user = self.session.query(User).filter(
                            User.guid == user.guid).one()

                    db_user.account = user.account
                    db_user.name = user.name

                    self.session.commit()
                except:
                    self.session.add(user)
                    self.session.commit()

        # Update data from status providers
        for provider in self.provider_instances['status']:
            while len(provider.updates):
                update = provider.updates.popleft()

                self.logger.info("Got update: %s" % update)

                try:
                    user = self.session.query(User).filter(
                            User.account == update['account']).one()

                    self.update_status(user, update['provider'],
                            update['status'], update['time'])
                except Exception as e:
                    self.logger.error("Unable to update status: %s" \
                            % update)

                    self.logger.exception(e)

        # Update data from device providers
        devices = defaultdict(list)

        for provider in self.provider_instances['devices']:
            for device in provider.devices:
                devices[device].append(str(provider))

        users = self.session.query(User)

        self.logger.debug("Found users: %s" % pformat(users))

        # Iterate through each user
        for user in users:
            # Iterate through all the user's devices and see
            # if any of them are active
            for device in user.devices:
                self.logger.debug("User has device: %s" % device)

                if device.mac_address in devices:
                    for provider in devices[device.mac_address]:
                        self.update_status(user, provider, 'in',
                                dt.now())
                else:
                    for provider in devices[device.mac_address]:
                        self.update_status(user, provider, 'out',
                                dt.now())

    def loop(self):
        """The main program loop."""

        while True:
            self.query_providers()

            time.sleep(10)

    def run_as_daemon(self):
        """Run people poker as a daemon process."""

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

@plac.annotations(
    daemonize=("Daemonize the People Poker service", 'flag', 'd'),
    configuration=("The configuration set to use", 'option', 'c'))
def main(daemonize=False, configuration=""):
    if configuration:
        configuration = "-%s" % configuration

    pp = PeoplePoker(configuration)

    if daemonize:
        pp.run_as_daemon()
    else:
        try:
            pp.loop()
        finally:
            for thread in pp.threads:
                print "Attempting to stop thread %s" % thread

                thread.stop()

if __name__ == "__main__":
    plac.call(main)
