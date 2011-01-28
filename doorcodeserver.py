import MySQLdb
import datetime
import re
import sys
import zmq

# TODO Refactor into a plugin class
# TODO Refactor to use a higher-level configuration library
# TODO Refactor to use SqlAlchemy
class DoorCodeProvider(Provider):
    def __init__(self, options=None):
        super(DoorCodeProvider, self).__init__()

    def start_server(self):
        """
        A ZeroMQ based server that will receive updates from the door server.
        """

        context = zmq.Context()

        # Provide default values
        host = ''
        port = 0

        try:
            socket = context.socket(zmq.REP)
            socket.bind(self.settings['uri'])
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

    def process_data(self, msg):
        try:
            db = MySQLdb.connect(
                host=self.settings['host'],
                user=self.settings['user'],
                passwd=self.settings['password'],
                db=self.settings['database'])

            cursor = db.cursor()

            now = datetime.datetime.now()

            # Assume user exists
            cursor.execute("""UPDATE current_user_status
                              SET status = "IN", last_seen = %s
                              WHERE userid = %s
                           """ , (now, msg.userid))

            return { 'Status': 'Success' }
        except MySQLdb.Error as e:
            return { 'Status': 'Failure', 'Exception': e }

if __name__ == "__main__":
    server = DoorCodeProvider()

    server.start_server()
