from ldap_provider import LDAPProvider


def test_ldap_provides_users():
    """Make sure we can get a list of users."""

    l = LDAPProvider()

    assert(len(l.users) > 0)

    print "Users:"

    for user in l.users:
        print user
