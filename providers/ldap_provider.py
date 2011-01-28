import ldap
import os
import sys

from provider import Provider

class LDAPProvider(Provider):
    provides = ['users']
    users = []

    def __init__(self, options=None):
        super(LDAPProvider, self).__init__()

        self.get_user_ldap_info()

    def __iter__(self):
        return self.users

    def open_connection(self):
        """ Open connection to the LDAP server """
        try:
            l = ldap.initialize(self.settings['server_uri'])

            l.set_option(ldap.OPT_X_TLS_DEMAND, True)
            l.set_option(ldap.OPT_REFERRALS, 0)

            # Use hardcoded certificate file
            ldap.set_option(ldap.OPT_X_TLS_CACERTFILE, 'certificates/root-ca.crt')

            # For debugging information uncomment below
            l.set_option(ldap.OPT_DEBUG_LEVEL, 255)

            l.protocol_version = ldap.VERSION3

            l.simple_bind_s("%s\\%s" % (self.settings['ldap_root'], self.settings['username']), self.settings['password'])
        except ldap.LDAPError, e:
            print "An LDAP exception was encountered opening the connection: %s" % e

        return l

    def close_connection(self, l):
        """ Close connection to the LDAP server """
        try:
            l.unbind()
        except ldap.LDAPError, e:
            print "An LDAP exception was encountered while closing connection: %s" % e

    def get_user_ldap_info(self):
        """ Extract user information from our ldap server """
        l = self.open_connection()

        # Example search to find a specific username:
        r = l.search_s(self.settings['ou_to_search'],
                       ldap.SCOPE_SUBTREE,
                       "(sAMAccountName=*)",
                       ['cn', 'sAMAccountName'])

        usernames = []

        for entry, attribute in r:
            usernames.append((attribute['sAMAccountName'][0], attribute['cn'][0]))

        self.users = usernames

        self.close_connection(l)