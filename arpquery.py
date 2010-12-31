## Python wrapper to probe the ARP caches of our routers and access points

## Dependencies:
##  snmpwalk system command
import os
import re

class Arp(Plugin):
    def poll(self):
        pass

    def serve(self):
        pass

def getArpCaches(devices_to_query, snmp_community, snmp_arp_variable):
    """ Query list of devices for active mac addresses. """
    # Start with an empty list of mac addresses
    mac_addrs = []

    for device in devices_to_query:
        lines = os.popen("snmpwalk -c " + snmp_community + " " +
               device + " " + snmp_arp_variable)

        for line in lines:
            # Get the MAC address at end of each line and add it to our list
            mac_addr = re.search('([0-9a-f:]*)$', line).group(0)
            mac_addr = validateAndNormalizeMacAddr(mac_addr)

            if mac_addr != None:
                mac_addrs.append(mac_addr)

    # Now that we have a list of the active users, create a 
    # set for fast lookup
    return set(mac_addrs)

def validateAndNormalizeMacAddr(addr):
    """ Validate and normalize addr into MAC lowercase, two digits per group.

    Validate that address is a valid MAC address. Nomralize the address to
    lowercase, and two digits per group for easy string comparison.
    """

    #Validation
    if re.match('(([0-9a-f]{1,2}:){5})([0-9a-f]{1,2})$',addr.lower()):
        # Validated ok, now normalize
        return ":".join([i.zfill(2) for i in addr.split(":")]).lower()
    else:
        print "Address " + addr + "not a valid MAC address"

        return None
