#!/usr/bin/env python
import ldap
import os
import sys

def open_connection(username, password, serverURI, ldaproot):
    """ Open connection to the LDAP server """
    try:
        l = ldap.initialize(serverURI)

        l.set_option(ldap.OPT_X_TLS_DEMAND, True)
        l.set_option(ldap.OPT_REFERRALS, 0)

        # Use hardcoded certificate file
        ldap.set_option(ldap.OPT_X_TLS_CACERTFILE, '/etc/openldap/cacerts/root-ca.crt')

        # For debugging information uncomment below
        l.set_option(ldap.OPT_DEBUG_LEVEL, 255)

        l.protocol_version = ldap.VERSION3

        l.simple_bind_s("%s\\%s" % (ldaproot, username), password)
    except ldap.LDAPError, e:
        print "An LDAP exception was encountered opening the connection: %s" % e

    return l

def close_connection(l):
    """ Close connection to the LDAP server """
    try:
        l.unbind()
    except ldap.LDAPError, e:
        print "An LDAP exception was encountered while closing connection: %s" % e

def get_user_ldap_info(username,password,serverURI,ldaproot,ou_to_search):
    """ Extract user information from our ldap server """
    l = open_connection(username,password,serverURI,ldaproot)

    # Example search to find a specific username:
    r = l.search_s(ou_to_search,
                   ldap.SCOPE_SUBTREE,
                   "(sAMAccountName=*)",
                   ['cn','sAMAccountName'])

    usernames = []

    for entry, attrib in r:
        usernames.append((attrib['sAMAccountName'][0], attrib['cn'][0]))

    close_connection(l)

    return usernames
