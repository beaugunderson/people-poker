import ldapconnect
import arpquery
import MySQLdb


#1. Get all users via LDAP. 
#2. Get ARP data for each access point
#3. For each user
# a) if arp data of any device is present, mark user as IN, 
# b) otherwise, mark as OUT

def userstatus():
    # Get all users
    names = ldapconnect.get_user_ldap_info()
    # Get all devices currently active
    active_devices = arpquery.getArpCaches()
    
    dbconn = MySQLdb.connect(host="localhost",
                             user = "",
                             passwd = "",
                             db = "test"
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
        ##Iterate through all the user's devices, and see if any of them are active
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

