## Python wrapper to probe the ARP caches of our routers and access points

## Dependencies:
##  snmpwalk system command
import os
import re

class Arp(StatusProvider):
    def __init__(self, options=None):
        pass

    def poll(self):
        mac_addresses = []

        for device in devices_to_query:
            mac_addresses += self._get_arp_cache(device)

    def _get_arp_cache(self, device):
        """
        Query a device for active mac addresses.
        """

        lines = os.popen("snmpwalk -c " + snmp_community + " " +
               device + " " + snmp_arp_variable)

        mac_addresses = []

        for line in lines:
            mac_address = re.search('([0-9a-f:]*)$', line).group(0)
            mac_address = self.validate_and_normalize(mac_address)

            if mac_address:
                mac_addresses.append(mac_address)

        return set(mac_addresses)

    def _validate_and_normalize(self, mac_address):
        """
        Validate that address is a valid MAC address. Normalize the address to
        lowercase and two digits per group for easy string comparison.
        """

        if re.match(r"(([0-9a-f]{1,2}:){5})([0-9a-f]{1,2})$", addr.lower()):
            return ":".join([i.zfill(2) for i in addr.split(":")]).lower()
        else:
            print "Address " + addr + " not a valid MAC address"

            return None
