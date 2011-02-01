import re
import zmq

from configobj import ConfigObj

def connect_and_send_userid(userid):
    config = ConfigObj("door-code.ini")

    context = zmq.Context()
    socket = context.socket(zmq.REQ)

    socket.connect(config["door-code-client"]["server_uri"])
    socket.send_json({ 'userid': userid })

    response = socket.recv_json()

    print "Response: %s" % response

if __name__ == "__main__":
    connect_and_send_userid("beau")
