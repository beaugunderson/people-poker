import json

from datetime import datetime as dt
from pprint import pprint

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models import ModelEncoder, Device, User, Status
from providers.ldap_provider import LDAPProvider


class TestLDAPProvider():
    """Test the LDAPProvider module"""

    def setup(self):
        print

    def test_ldap_provides_users(self):
        """Make sure we can get a list of users"""

        l = LDAPProvider()
        l.poll()

        print json.dumps(l.users, cls=ModelEncoder, indent=4)

        assert len(l.users) > 0


class TestModels():
    """Test our models and SqlAlchemy functionality"""

    def setup(self):
        """Setup the in-memory sqlite engine."""

        print

        self.engine = create_engine('sqlite:///:memory:', echo=False)

        User.metadata.create_all(self.engine)
        Device.metadata.create_all(self.engine)

        Session = sessionmaker()
        Session.configure(bind=self.engine)

        self.session = Session()

    def test_create_user(self):
        """Create a user from arguments"""

        u = User('user1', 'user1_guid', 'Jon Doe', 'Jon', 'Doe', 'Department',
                'jon@doe.com')

        assert repr(u) == "<User(None, 'user1', 'Jon Doe', 'user1_guid')>"

    def test_create_device(self):
        """Create a device from arguments"""

        d = Device('abc', 'aa:bb:cc:dd:ee')

        assert repr(d) == "<Device(None, 'abc', 'aa:bb:cc:dd:ee')>"

    def test_create_status(self):
        """Create a status update from arguments"""

        time = dt.now()

        s = Status('status-provider', 'in', time)

        assert repr(s) == "<Status(None, 'status-provider', 'in', '%s')>" \
                % time

    def test_device_query(self):
        """Create a device and assure that it's queryable and identitical"""

        d1 = Device('abc', 'aa:bb:cc:dd:ee')

        self.session.add(d1)

        assert self.session.query(Device).filter_by(name='abc').count() == 1
        assert self.session.query(Device).filter_by(name='abc').one()

        d2 = self.session.query(Device).filter_by(name='abc').one()

        assert d1 == d2

        assert repr(d1) == "<Device(1, 'abc', 'aa:bb:cc:dd:ee')>"
        assert repr(d2) == "<Device(1, 'abc', 'aa:bb:cc:dd:ee')>"

    def test_device_not_exists(self):
        """Query for a non-existent device and assure that the count is 0"""

        assert self.session.query(Device).filter_by(name='def').count() == 0

    def test_commit(self):
        """Commit to the sqlite:///:memory: store"""

        self.session.commit()

    def test_relationship(self):
        """Test relationships between users, devices, and statuses"""

        u = User('user1', 'user1_guid', 'Jon Doe', 'Jon', 'Doe', 'Department',
                'jon@doe.com')
        d = Device('device1', 'aa:bb:cc:dd:ee')
        s = Status('status-provider', 'in', dt.now())

        self.session.add(s)
        self.session.add(u)
        self.session.add(d)

        d.user = u
        s.user = u

        self.session.commit()

        pprint(u)
        pprint(d)
        pprint(s)

        pprint(u.devices)
        pprint(u.statuses)

        assert d.user == u
        assert d in u.devices

        assert s.user == u
        assert s in u.statuses

        assert u.devices[0] == d
        assert u.statuses[0] == s
