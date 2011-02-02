import json
import sys
import threading
import zmq

from zmq.eventloop import ioloop, zmqstream

from spp.provider import Provider


class ZMQServerProvider(Provider, threading.Thread):
    provides = ['status', 'server']
    updates = []

    def __init__(self, args=(), kwargs={}):
        super(ZMQServerProvider, self).__init__(*args, **kwargs)

        self.loop = ioloop.IOLoop.instance()

    def stop(self):
        self.loop.stop()

    def receive(self, message):
        message = json.loads(''.join(message))

        print "Received message: %s" % message

        if 'user_id' in message:
            self.updates.append(message)

            self.stream.send_json({'status': 'ok'})
        else:
            print "Received bad data: %s" % message

    def run(self):
        """
        A ZeroMQ based server that receives updates from clients like the door
        code provider.
        """

        context = zmq.Context()

        try:
            socket = context.socket(zmq.REP)
            socket.bind(self.settings['server_uri'])
        except zmq.ZMQError as e:
            print "Could not bind to socket " \
                "using %s: %s" % (self.settings['server_uri'], e)

            sys.exit(1)

        self.stream = zmqstream.ZMQStream(socket, self.loop)

        print "zme.REP socket opened at %s" % self.settings['server_uri']

        self.stream.on_recv(self.receive)
        self.loop.start()

if __name__ == "__main__":
    server = ZMQServerProvider()

    try:
        server.start()
    finally:
        server.stop()
