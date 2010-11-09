#!/usr/bin/env python
import ldap
import os
import sys


## Magic credentials from Beau
username = "app-test"
password = "pZ98j3pZ98j3"

def open_connection():
    try:
        l = ldap.initialize('ldaps://sanjuan.synapsedev.com:636')
    
        l.set_option(ldap.OPT_X_TLS_DEMAND, True)
        l.set_option(ldap.OPT_REFERRALS, 0)

        # Use hardcoded certificate file
        ldap.set_option(ldap.OPT_X_TLS_CACERTFILE, '/etc/openldap/cacerts/root-ca.crt')

        # For debugging information uncomment below
        l.set_option(ldap.OPT_DEBUG_LEVEL, 255)
 
        l.protocol_version = ldap.VERSION3
 
        l.simple_bind_s("SYNAPSEDEV\%s" % username, password)

    except ldap.LDAPError, e:
        print "An LDAP exception was encountered opening the connection: %s" % e

    return l

def close_connection(l):
    try:
         l.unbind()
    except ldap.LDAPError, e:
        print "An LDAP exception was encountered while closing connection: %s" % e


def get_user_ldap_info():

    l = open_connection()
 
    # Example search to find a specific username:
    r = l.search_s("OU=MyBusiness,DC=synapsedev,DC=com", 
                   ldap.SCOPE_SUBTREE, 
                   "(sAMAccountName=*)",
                   ['cn','sAMAccountName']
                   )
    close_connection(l)

    return r

