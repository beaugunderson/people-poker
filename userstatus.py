import ldapconnect
import arpquery
import MySQLdb
import daemon
import sys
import time
import ConfigParser
import datetime

def update_user_status():
    """ Update database with current user status.

    Query ARP cache for access points, 
    Get list of users from LDAP server
    Update MYSQL database with the new status, inserting new users if necessary
    
    """

    # Read config file each time function is called
    config = ConfigParser.ConfigParser()
    config.read("config.ini")

    # Get all users
    names = ldapconnect.get_user_ldap_info(
        config.get('LDAPInfo','username'),
        config.get('LDAPInfo','password'),
        config.get('LDAPInfo','serverURI'),
        config.get('LDAPInfo','ldaproot'),
        config.get('LDAPInfo','ou_to_search')
        )

    # Get all devices currently active
    active_devices = arpquery.getArpCaches(
        #devices_to_query appears as comma separated list, so
        # get rid of the commas.
        config.get('SNMPInfo','devices_to_query').split(','),
        config.get('SNMPInfo','snmp_community'),
        config.get('SNMPInfo','snmp_arp_variable')
        )

    dbconn = MySQLdb.connect(
        host = config.get("DBInfo" , "host"),
        user = config.get("DBInfo" , "user"),
        passwd = config.get("DBInfo" , "password"),
        db = config.get("DBInfo" , "dbname")
        )

    cursor = dbconn.cursor()

    for userid,name in names:
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
                           """, (userid,user_status,now) )
        else:
            #User did exist, update row
            cursor.execute("""UPDATE current_user_status 
                              SET status = %s, last_seen = %s 
                              WHERE userid = %s 
                           """ , (user_status,now, userid) )

    #Sleep until time to poll again
    try:
        time.sleep(float(config.get("PollInfo" , "frequency_seconds")))
    except ValueError:
        #Poll every minute by default
        time.sleep(60)

def people_poker_loop():
    """ Main loop for the people poker.

    """
    while True:
        print "Querying status"
        update_user_status()


def people_poker_daemon():
    """ Run people poker as daemon process 

    """
    print "Starting PeoPlePoker daemon"
    myerr = open('/Users/peter/Workspace/peoplepoker/err.log','w+')
    myout = open('/Users/peter/Workspace/peoplepoker/out.log','w+')

    with daemon.DaemonContext(stdout = myout, 
                              stderr = myerr,
                              working_directory = '/Users/peter/Workspace/peoplepoker/'):
        people_poker_loop()

    # Clean up any open files.
    myerr.close()
    myout.close()


if __name__ == "__main__":
    people_poker_daemon()
