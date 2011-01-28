from device import Device
from user import User

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

class TestDevice():
    def setup(self):
        """Setup the in-memory sqlite engine."""

        self.engine = create_engine('sqlite:///:memory:', echo=False)

        User.metadata.create_all(self.engine)
        Device.metadata.create_all(self.engine)

        Session = sessionmaker()
        Session.configure(bind=self.engine)

        self.session = Session()

    def test_create_device(self):
        d = Device('abc', 'aa:bb:cc:dd:ee')

    def test_device_query(self):
        d = Device('abc', 'aa:bb:cc:dd:ee')

        print "Device: %s" % d

        self.session.add(d)

        assert self.session.query(Device).filter_by(name='abc').count() == 1

    def test_device_not_exists(self):
        assert self.session.query(Device).filter_by(name='def').count() == 0

    def test_commit(self):
        self.session.commit()

    def test_relationship(self):
        """Test that relationships between users and devices work."""

        u = User('user1')
        d = Device('device1', 'aa:bb:cc:dd:ee')

        self.session.add(u)
        self.session.add(d)

        d.user = u

        self.session.commit()

        assert d.user == u
        assert d in u.devices