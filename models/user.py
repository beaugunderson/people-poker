from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey

from models import Base

class User(Base):
    __tablename__ = 'users'
    __table_args__ = { 'useexisting': True }

    id = Column(Integer, primary_key=True)
    username = Column(String)

    def __init__(self, username):
        self.username = username

    def __repr__(self):
        return "<User('%s')>" % (self.username)
