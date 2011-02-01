import os
import re

from provider import Provider


class ArpProvider(Provider):
    provides = ['devices']

    def __init__(self):
        super(ArpProvider, self).__init__()

    def poll(self):
        mac_addresses = []

        for device in self.settings.keys():
            #print "Querying device: %s" % device

            mac_addresses += self._get_arp_cache(device, self.settings[device])

        self.devices = list(set(mac_addresses))
        self.devices.sort()

    def _get_arp_cache(self, device, settings):
        """Query a device for active MAC addresses."""

        command = "snmpwalk -v1 -c %s %s %s" % (settings['community'], device,
            settings['arp_variable'])

        lines = os.popen(command)

        mac_addresses = []

        for line in lines:
            mac_address = re.search('([0-9a-fA-F ]*)$', line).group(0).strip()
            mac_address = self._validate_and_normalize(mac_address)

            if mac_address:
                mac_addresses.append(mac_address)

        return set(mac_addresses)

    def _validate_and_normalize(self, mac_address):
        """
        Validate that address is a valid MAC address. Normalize the address to
        lowercase and two digits per group for easy string comparison.
        """

        if re.match(r"(([0-9a-f]{1,2}[: ]){5})([0-9a-f]{1,2})$",
            mac_address.lower()):
            return ":".join([i.zfill(2) for i in re.split(r"[: ]",
                mac_address)]).lower()
        else:
            print mac_address + " is not a valid MAC address"

            return None
