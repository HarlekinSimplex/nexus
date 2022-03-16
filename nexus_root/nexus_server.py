import sys
import argparse
import RNS
from http.server import HTTPServer, ThreadingHTTPServer, BaseHTTPRequestHandler
from http import HTTPStatus
import json
import time

# Sample message store
#
# messageStore = [
#    {'time': '2022-03-01 23:48:39', 'msg': 'Static Test Message #1', 'id': 1646174919000},
#    {'time': '2022-03-01 23:52:51', 'msg': 'Static Test Message #2', 'id': 1646175171000},
#    {'time': '2022-03-01 23:52:53', 'msg': 'Static Test Message #3', 'id': 1646175173000},
# ]

messageStore = [
]

MESSAGE_BUFFER_SIZE = 20
DEBUG = False

APP_NAME = "nexus"
NEXUS_SERVER_ADDRESS = ('', 4281)
NEXUS_SERVER_ASPECT = "deltamatrix"
NEXUS_SERVER_IDENTITY = None


def initialize_server(configpath, server_port=None, server_apspect=None):
    global NEXUS_SERVER_ADDRESS
    global NEXUS_SERVER_ASPECT
    global NEXUS_SERVER_IDENTITY

    RNS.Reticulum(configpath)

    if server_port is not None:
        NEXUS_SERVER_ADDRESS = ('', int(server_port))

    if server_apspect is not None:
        NEXUS_SERVER_ASPECT = server_apspect

    RNS.log(
        "Server Parameter --port:"+str(NEXUS_SERVER_ADDRESS[1])+" --aspect:"+NEXUS_SERVER_ASPECT
    )

    NEXUS_SERVER_IDENTITY = RNS.Identity()
    server_destination = RNS.Destination(
        NEXUS_SERVER_IDENTITY,
        RNS.Destination.IN,
        RNS.Destination.SINGLE,
        APP_NAME,
        NEXUS_SERVER_ASPECT
    )
    announce_handler = AnnounceHandler(
        aspect_filter=APP_NAME + '.' + NEXUS_SERVER_ASPECT
    )
    RNS.Transport.register_announce_handler(announce_handler)
    server_destination.set_packet_callback(packet_callback)
    server_destination.announce(app_data=(APP_NAME+'.'+NEXUS_SERVER_ASPECT).encode("utf-8"))
    run_server()


def run_server():
    global NEXUS_SERVER_ASPECT
    global NEXUS_SERVER_ADDRESS

    httpd = ThreadingHTTPServer(NEXUS_SERVER_ADDRESS, ServerRequestHandler)
    RNS.log(
        "serving Nexus aspect <" + NEXUS_SERVER_ASPECT + "> at %s:%d" % NEXUS_SERVER_ADDRESS
    )
    httpd.serve_forever()


class AnnounceHandler:
    # The initialisation method takes the optional
    # aspect_filter argument. If aspect_filter is set to
    # None, all announces will be passed to the instance.
    # If only some announces are wanted, it can be set to
    # an aspect string.
    def __init__(self, aspect_filter=None):
        self.aspect_filter = aspect_filter

    # This method will be called by Reticulums Transport
    # system when an announcement arrives that matches the
    # configured aspect filter. Filters must be specific,
    # and cannot use wildcards.
    def received_announce(self, destination_hash, announced_identity, app_data):
        RNS.log(
            "Received an announce from " +
            RNS.prettyhexrep(destination_hash)
        )

        RNS.log(
            "The announce contained the following app data: " +
            app_data.decode("utf-8")
        )

        remote_server = RNS.Destination(
            announced_identity,
            RNS.Destination.OUT,
            RNS.Destination.SINGLE,
            APP_NAME,
            NEXUS_SERVER_ASPECT
        )

        RNS.Packet(remote_server, '{"id":4711, "msg":"Hello World"}', create_receipt=False).send()


def packet_callback(data, packet):
    # Simply print out the received data
    print("")
    print("Received data: " + data.decode("utf-8") + "\r\n> ", end="")
    sys.stdout.flush()


class ServerRequestHandler(BaseHTTPRequestHandler):

    # Borrowing from https://gist.github.com/nitaku/10d0662536f37a087e1b
    def _set_headers(self):
        # Set response result code and data format
        self.send_response(HTTPStatus.OK)
        self.send_header('Content-type', 'application/json')
        # Allow requests from any origin, so CORS policies don't
        # prevent local development.
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

    def do_GET(self):
        self._set_headers()
        self.wfile.write(json.dumps(messageStore).encode('utf-8'))

    def do_POST(self):
        # ToDo: Need to implement more features:
        #    ClearBuffer command
        #
        # Get length of POST message, read those bytes and parse it as JSON string into a message
        # and append that string to the message store
        length = int(self.headers.get('content-length'))
        message = json.loads(self.rfile.read(length))
        # Create a timestamp and add that to the message map
        message['id'] = int(time.time() * 100000)

        #        # append the JSON message map to the message store at first position
        #        messageStore.insert(0, message)
        #        # Check store size if defined limit is reached
        #        length = len(messageStore)
        #        if length > MESSAGE_BUFFER_SIZE:
        #            # If limit is exceeded just drop first (oldest) element of list
        #            messageStore.pop(len(messageStore))

        # append the JSON message map to the message store at last position
        messageStore.append(message)
        # Check store size if defined limit is reached
        length = len(messageStore)
        if length > MESSAGE_BUFFER_SIZE:
            # If limit is exceeded just drop first (oldest) element of list
            messageStore.pop(0)

        print(message)

        # DEBUG: Log actual message store to console
        if DEBUG:
            for s in messageStore:
                print(s)

        # Build and return JSON success response
        self._set_headers()
        self.wfile.write(json.dumps({'success': True}).encode('utf-8'))

    # Send to reticulum

    def do_OPTIONS(self):
        # Send allow-origin header and clearance for GET and POST requests
        self.send_response(HTTPStatus.NO_CONTENT)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST')
        self.send_header('Access-Control-Allow-Headers', 'content-type')
        self.end_headers()


#######################################################
# Program Startup
#

if __name__ == "__main__":
    try:
        parser = argparse.ArgumentParser(
            description="Minimal Nexus Message Server"
        )

        parser.add_argument(
            "--config",
            action="store",
            default=None,
            help="path to alternative Reticulum config directory",
            type=str
        )

        parser.add_argument(
            "--port",
            action="store",
            default=None,
            help="server port to listen for http/post and http/get requests",
            type=str
        )

        parser.add_argument(
            "--aspect",
            action="store",
            default=None,
            help="reticulum aspect to configer server replication topology",
            type=str
        )

        params = parser.parse_args()

        if params.config:
            config_para = params.config
        else:
            config_para = None

        if params.port:
            port_para = params.port
        else:
            port_para = None

        if params.aspect:
            aspect_para = params.aspect
        else:
            aspect_para = None

        initialize_server(config_para, port_para, aspect_para)

    except KeyboardInterrupt:
        print("")
        exit()
