import ldapconnect
import arpquery
import MySQLdb
import daemon
import sys
import time

import ConfigParser

def update_user_status():
    """ Update database with current user status.

    Query ARP cache for access points, 
    Get list of users from LDAP server
    Update MYSQL database with the new status, inserting new users if necessary
    
    """

    # Read config file 
    config = ConfigParser.ConfigParser()
    config.read("config.ini")

    # Get all users
    names = ldapconnect.get_user_ldap_info(
        config.get('LDAPInfo','username'),
        config.get('LDAPInfo','password'),
        config.get('LDAPInfo','serverURI'),
        config.get('LDAPInfo','ldaproot'))

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

    for dn,attributes in names:
        userid = attributes["sAMAccountName"]
        user_devices = cursor.execute("""
            SELECT deviceaddr FROM userdevices 
            WHERE userid = %s
            """,  (userid) )
        
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
            """,  (userid) )
        print "PROCESSING" , user_status , userid
        if cursor.fetchall() == () :
            ## User did not exist in table yet. Add user.
            cursor.execute("""INSERT INTO current_user_status 
                              VALUES (%s, %s)
                           """, (userid[0],user_status) )
        else:
            #User did exist, update row
            cursor.execute("""UPDATE current_user_status 
                              SET status = %s 
                              WHERE userid = %s 
                           """ , (user_status,userid[0]) )


def people_poker_loop():
    """ Main loop for the people poker.

    """
    while True:
        print "Querying status"
        ## TBD read config file
        update_user_status()
        time.sleep(10)
        

def people_poker_daemon():
    """ Run people poker as daemon process 

    """
    print "Starting Peoplepoker daemon"
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
