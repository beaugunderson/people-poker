import socket
import ConfigParser
import re

def connect_and_send_userid(userid):
    # Read config file
    try:
        config = ConfigParser.ConfigParser()
        config.read('config.ini')

        HOST = config.get('DOOR_CODE','serverURI')  # The remote host
        PORT = int(config.get('DOOR_CODE','port'))  # The same port as used by the server

    #Catch the baseclass exception only
    except ConfigParser.Error:
        print "Could not read config file"

        return

    try:
        #IPv4 compatible only
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((HOST, PORT))
        s.send(userid)
        s.close()
    except IOError:
        print "Could not connect to socket"
        return

if __name__ == "__main__":
    connect_and_send_userid("peter")
