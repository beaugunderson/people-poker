## Python wrapper to probe the ARP caches of our routers and access points

## Dependencies:
##  snmpwalk system command
## configuration file with router/access point names.

import os
import re
import ConfigParser

snmpcmd = "snmpwalk"
#snmp_community = "-c dvd300i"
#snmp_arp_variable  = "ip.ipNetToMediaTable.ipNetToMediaEntry.ipNetToMediaPhysAddress"

#servers = ["valhalla","los_angeles", "new_york"]

users = [('peter', '34:15:9e:02:c2:b8'), 
         ('chewbacca', '34')
]

current_user_status = [('peter', '', '', ''),
                       ('chewbacca', '', '', ''),
                       ('luke', '', '', ''),
                       ('darth', '', '', '')
                       ]



###
# Read config file config.ini
###
configFileName = 'config.ini'
def readConfigFile():
    config = ConfigParser.ConfigParser()
    config.read(configFileName)
    community = config.get('SNMP','snmp_community')
    var = config.get('SNMP','snmp_arp_variable')

    arpDevices = config.get('SNMP','arpDevices')
    arpDevices = arpDevices.split(',')

    return (community,var,arpDevices)


### 
# Validate and normalize each mac address
###
def getArpCaches():

    (snmp_community,snmp_arp_variable,arpservers) = readConfigFile()


    # Start with an empty list of mac addresses
    macAddrs = []
    for server in arpservers:
        lines = os.popen("snmpwalk -c " + snmp_community + " " +
               server + " " + snmp_arp_variable)
        for line in lines: 
            # Get the MAC address at end of each line and add it to our list
            addr = re.search('([0-9a-f:]*)$', line).group(0)
            addr = validateAndNormalizeMacAddr(addr)
            if addr != None:
                macAddrs.append(addr)



    ## Now that we have a list of the active users, create a 
    ## set for fast lookup
    macSet = set(macAddrs)

    return macSet
    #### Now look through our db of users, and determine who is in, and 
    #### who is out
#    for user,addr in users:
#        if addr in macSet:
#            print user + " is in because " + addr + " is in the set"
#        else:
#            print user + " is NOT in because " + addr + " is not in the set"

## 
# Validate and normalize each mac address
##
def validateAndNormalizeMacAddr(addr):
    #Validate MAC addrss, and if necessary insert 0s to make sure 
    # address is in two digits per colon

    ###Validation
    if re.match('(([0-9a-f]{1,2}:){5})([0-9a-f]{1,2})$',addr.lower()):
        # Address is a valid MAC address. Now normalize it
        return ":".join([i.zfill(2) for i in addr.split(":")]).lower()
    else:
        print "Address " + addr + "not a valid MAC address"
        return None



import ldap
def ldapsearch():
    l = ldap.initialize("ldap://synapsedev.com")
    l.search_s("",ldap.SCOPE_SUBTREE,'(cn=peter*)',['cn','mail'])
