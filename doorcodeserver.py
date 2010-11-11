import socket
import MySQLdb
import ConfigParser
import datetime
import re

def start_server():
    """ IPv4 server to receive occasional door code updates.

    The packet sent by client should be a simple string of the username
    """

    #Provide default values
    host = ''
    port = 0
    try:
        # Read config file
        config = ConfigParser.ConfigParser()
        config.read("config.ini")
        host = ''       # Symbolic name meaning all available interfaces
        port = int(config.get("DOOR_CODE","port"))
    except ConfigParser.Error:
        print "Could not read config file"
        return

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((host, port)) 
    except IOError:
        print "Could not open socket"
        return

    while(1):
        try:
            s.listen(1)
            conn, addr = s.accept()
            print 'Connected by', addr

            # No packet should be larger than 1024 bytes in this case
            userid = conn.recv(1024)
            if userid:
                print "received data"
                process_data(userid)
            else:
                print "received bad data, discarding"
            #Close and wait for new connection
            conn.close()
        except IOError:
            print "Could not accept connection from client"


def process_data(userid):

    try:
        config = ConfigParser.ConfigParser()
        config.read("config.ini")
        

        # Validate the data to be < 30 characters, and only digits and ascii characters
        if len(userid)<=30 and re.match("^[a-z0-9A-Z_.]*$",userid):
            dbconn = MySQLdb.connect(
                host = config.get("DBInfo" , "host"),
                user = config.get("DBInfo" , "user"),
                passwd = config.get("DBInfo" , "password"),
                db = config.get("DBInfo" , "dbname")
                )

            cursor = dbconn.cursor()

            now = datetime.datetime.now()
            # Assume user exists
            cursor.execute("""UPDATE current_user_status 
                              SET status = "IN", last_seen = %s 
                              WHERE userid = %s 
                           """ , (now, userid) )

        else:
            #data recieved did not match our format
            print "Rejected username" , userid
    except ConfigParser.Error:
        print "Could not read config file"
    except MySQLdb.Error:
        print "Could not access MySQL database"


if __name__ == "__main__":
    start_server()
