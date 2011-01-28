import arpquery
import daemon
import datetime
import ldapconnect
import MySQLdb
import sys
import time

def update_user_status():
    """ Update database with current user status.
    Query ARP cache for access points,
    Get list of users from LDAP server
    Update MYSQL database with the new status, inserting new users if necessary
    """

    # Read config file each time function is called

    # Get all users
    names = ldapconnect.get_user_ldap_info(
        self.settings[('ldap','username')],
        self.settings[('ldap','password')],
        self.settings[('ldap','server_uri')],
        self.settings[('ldap','ldaproot')],
        self.settings[('ldap','ou_to_search')])

    # Get all devices currently active
    active_devices = arpquery.getArpCaches(
        #devices_to_query appears as comma separated list, so
        # get rid of the commas.
        self.settings[('snmp', 'devices_to_query')].split(','),
        self.settings[('snmp', 'snmp_community')],
        self.settings[('snmp', 'snmp_arp_variable')])

    dbconn = MySQLdb.connect(
        host=self.settings[("database", "host")],
        user=self.settings[("database", "user")],
        passwd=self.settings[("database", "password")],
        db=self.settings[("database", "dbname")])

    cursor = dbconn.cursor()

    for userid, name in names:
        user_devices = cursor.execute("""
            SELECT deviceaddr FROM userdevices
            WHERE userid = %s
            """,  userid )

        user_status = 'OUT'

        devs = cursor.fetchall()

        # Iterate through all the user's devices, and see
        # if any of them are active
        for dev in devs:
            if dev[0] in active_devices:
                user_status = 'IN'
                break

        ##Do the check to see if user exist in the current_user_status table
        cursor.execute("""
            SELECT status FROM current_user_status
            WHERE userid = %s
            """,  userid )

        #TBD Need to be more specific about semantics of last_seen and IN/OUT
        now = datetime.datetime.now()

        if cursor.fetchall() == () :
            ## User did not exist in table yet. Add user.
            cursor.execute("""INSERT INTO current_user_status
                              VALUES (%s, %s, %s)
                           """, (userid,user_status,now))
        else:
            #User did exist, update row
            cursor.execute("""UPDATE current_user_status
                              SET status = %s, last_seen = %s
                              WHERE userid = %s
                           """ , (user_status,now, userid))

    #Sleep until time to poll again
    try:
        time.sleep(float(self.settings[("poller" , "frequency_seconds")]))
    except ValueError:
        #Poll every minute by default
        time.sleep(60)

def people_poker_loop():
    """ Main loop for the people poker. """
    while True:
        print "Querying status"

        update_user_status()

def people_poker_daemon():
    """ Run people poker as daemon process """
    print "Starting People Poker daemon"

    logs = os.path.join(os.getcwd(), "logs")

    try:
        os.mkdir(logs)
    except:
        pass

    error_log = open(os.path.join(logs, 'error.log'), 'w+')
    output_log = open(os.path.join(logs, 'output.log'), 'w+')

    with daemon.DaemonContext(stdout=output_log,
                              stderr=error_log,
                              working_directory=os.getcwd()):
        people_poker_loop()

    # Clean up any open files.
    error_log.close()
    output_log.close()

if __name__ == "__main__":
    people_poker_daemon()
