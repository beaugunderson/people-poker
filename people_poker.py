import daemon
import datetime
import imp
import os
import pkgutil
import sys
import time

from collections import defaultdict

from models.user import User
from models.device import Device
from models.status import Status

from sqlalchemy import create_engine, ForeignKey, and_
from sqlalchemy.orm import backref, relationship, sessionmaker

from provider import Provider

class PeoplePoker(object):
    def __init__(self):
        self.providers = self.get_providers()

    def get_providers(self):
        plugin_path = [os.path.join(sys.path[0], 'providers')]

        for loader, name, ispkg in pkgutil.iter_modules(plugin_path):
            file, pathname, desc = imp.find_module(name, plugin_path)

            imp.load_module(name, file, pathname, desc)

        subclasses = Provider.__subclasses__()

        providers = defaultdict(list)

        for subclass in subclasses:
            print "Subclass %s provides %s" % (subclass, subclass.provides)

            for type in subclass.provides:
                providers[type].append(subclass)

        return providers

    def update_user_status(self, sleep=True):
        """
        Update database with current user status.
        Query ARP cache for access points,
        Get list of users from LDAP server
        Update MYSQL database with the new status, inserting new users if necessary
        """

        from pprint import pprint
        pprint(self.providers)

        user_providers = []
        for provider in self.providers['users']:
            user_providers.append(provider())

        # TODO change device to status, must map to a user?
        device_providers = []
        for provider in self.providers['devices']:
            device_providers.append(provider())

        # Initialize the database
        engine = create_engine('sqlite:///:memory:', echo=False)

        from models import Base
        Base.metadata.create_all(engine)

        Session = sessionmaker()
        Session.configure(bind=engine)

        session = Session()

        for provider in device_providers:
            print "Using provider: %s" % provider

            for device in provider.devices:
                print "Found device: %s" % device

        for user in session.query(User):
            print "Found user: %s" % user

            user_status = 'OUT'

            # Iterate through all the user's devices, and see
            # if any of them are active
            for device in user.devices:
                print "User had device: %s" % device

                for provider in device_providers:
                    if device.mac_address in provider.devices:
                        user_status = 'IN'

                        break

            try:
                status = session.query(Status).filter(_and(Status.user==user, Status.provider==provider)).one()

                status.provider = provider
                status.status = user_status
                status.update_time = now

                session.commit()
            except:
                now = datetime.datetime.now()

                status = Status(provider, user_status, now)

                session.add(status)
                session.commit()

        if sleep:
            time.sleep(60)

    def people_poker_loop(self):
        """ Main loop for the people poker. """
        while True:
            print "Querying status"

            self.update_user_status()

    def run_as_daemon(self):
        """Run people poker as daemon process"""

        print "Starting People Poker daemon"

        logs = os.path.join(os.getcwd(), "logs")

        try:
            os.mkdir(logs)
        except:
            pass

        error_log = open(os.path.join(logs, 'error.log'), 'w+')
        output_log = open(os.path.join(logs, 'output.log'), 'w+')

        providers = get_providers()

        with daemon.DaemonContext(stdout=output_log,
                                  stderr=error_log,
                                  working_directory=os.getcwd()):
            people_poker_loop()

        # Clean up any open files.
        error_log.close()
        output_log.close()

if __name__ == "__main__":
    pp = PeoplePoker()

    pp.update_user_status(sleep=False)
    #pp.run_as_daemon()
