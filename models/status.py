from sqlalchemy import Column, DateTime, Integer, String, MetaData, ForeignKey
from sqlalchemy.orm import backref, relationship

from models.user import User
from models import Base


class Status(Base):
    __tablename__ = 'statuses'
    __table_args__ = {'useexisting': True}

    id = Column(Integer, primary_key=True)
    provider = Column(String)
    status = Column(String)
    update_time = Column(DateTime)

    user = relationship(User, backref=backref('statuses'), order_by=id)
    user_id = Column(Integer, ForeignKey('users.id'))

    def __init__(self, name, update_time, status):
        self.provider = provider
        self.status = status
        self.update_time = update_time

    def __repr__(self):
        return "<Status('%s', '%s', '%s')>" % (self.provider, self.status,
                self.update_time)
