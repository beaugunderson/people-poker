from collections import defaultdict

from spp.models import User
from spp.provider import Provider

from spp.utilities import connect_and_search_ldap


class LDAPProvider(Provider):
    provides = ['users']
    users = []

    def __init__(self):
        super(LDAPProvider, self).__init__()

    def poll(self):
        self.users = self.get_user_ldap_info()

    def get_user_ldap_info(self):
        """Extract user information from our ldap server"""

        r = connect_and_search_ldap(self.settings,
                self.settings['ou_to_search'],
                "(sAMAccountName=*)",
                ['sAMAccountName', 'cn', 'objectGUID', 'manager', 'department',
                    'givenName', 'sn', 'mail'])

        users = []

        for dn, user in r:
            guid = ''.join(['%02X' % ord(c) for c in user['objectGUID'][0]])

            # In case a desired property is missing
            user = defaultdict(lambda: [''], user)

            users.append(User(account=user['sAMAccountName'][0], guid=guid,
                display_name=user['cn'][0], first_name=user['givenName'][0],
                last_name=user['sn'][0], department=user['department'][0],
                email=user['mail'][0], provider=self))

        return users
