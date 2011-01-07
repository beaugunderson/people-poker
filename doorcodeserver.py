import MySQLdb
import datetime
import re
import sys
import zmq

from ConfigParser import SafeConfigParser

# TODO Refactor into a plugin class
# TODO Refactor to use a higher-level configuration library
# TODO Refactor to use SqlAlchemy

def start_server():
    """ IPv4 server to receive occasional door code updates.

    The packet sent by client should be a simple string of the username
    """

    context = zmq.Context()

    # Provide default values
    host = ''
    port = 0

    try:
        # Read config file
        config = SafeConfigParser()
        config.read("config.ini")

        uri = config.get("DOOR_CODE", "server-uri")
    except ConfigParser.Error:
        print "Could not read config file"

       	sys.exit(1) 

    try:
        socket = context.socket(zmq.REP)
        socket.bind(uri)
    except zmq.ZMQError as e:
        print "Could not bind to socket using %s: %s" % (uri, e)

        sys.exit(1)

    print "zme.REP socket opened at %s" % uri

    while True:
        try:
            msg = socket.recv_json()

            if msg.userid:
                print "Received data: %s" % msg

                socket.send_json(process_data(msg))
            else:
                print "Received bad data, discarding"
        except IOError:
            print "Could not accept connection from client"

def process_data(msg):
    try:
        config = ConfigParser.ConfigParser()
        config.read("config.ini")

        dbconn = MySQLdb.connect(
            host = config.get("DBInfo" , "host"),
            user = config.get("DBInfo" , "user"),
            passwd = config.get("DBInfo" , "password"),
            db = config.get("DBInfo" , "dbname"))

        cursor = dbconn.cursor()

        now = datetime.datetime.now()

        # Assume user exists
        cursor.execute("""UPDATE current_user_status 
                          SET status = "IN", last_seen = %s 
                          WHERE userid = %s 
                       """ , (now, msg.userid))

	return { 'Status': 'Success' }
    except (ConfigParser.Error, MySQLdb.Error) as e:
        return { 'Status': 'Failure', 'Exception': e }

if __name__ == "__main__":
    start_server()
