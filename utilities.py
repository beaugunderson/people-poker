import ldap
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from spp.models import Base


def create_db_session(settings, echo=False):
    engine = create_engine(settings["server_uri"], echo=echo, pool_recycle=600)

    Base.metadata.create_all(engine)

    Session = sessionmaker()
    Session.configure(bind=engine)

    return Session()


def create_ldap_connection(settings):
    l = ldap.initialize(settings['server_uri'])

    l.set_option(ldap.OPT_X_TLS_DEMAND, True)
    l.set_option(ldap.OPT_REFERRALS, 0)

    # XXX Use hardcoded certificate file
    ldap.set_option(ldap.OPT_X_TLS_CACERTFILE,
            os.path.abspath('/usr/local/spp/certificates/root-ca.crt'))

    # For debugging information uncomment below
    l.set_option(ldap.OPT_DEBUG_LEVEL, 255)

    l.protocol_version = ldap.VERSION3

    l.simple_bind_s("%s\\%s" % (settings['ldap_root'],
        settings['username']),
        settings['password'])

    return l


def connect_and_search_ldap(settings, base_dn, query, attributes,
        scope=ldap.SCOPE_SUBTREE):
    l = create_ldap_connection(settings)

    r = l.search_s(base_dn, scope, query, attributes)

    l.unbind()

    return r
