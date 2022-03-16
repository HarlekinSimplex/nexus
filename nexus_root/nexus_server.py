##########################################################################################
#
# Nexus Message Server
#
#

import sys
import argparse
import RNS
from http.server import HTTPServer, ThreadingHTTPServer, BaseHTTPRequestHandler
from http import HTTPStatus
import json
import pickle
import time

# Sample message store
#
# messageStore = [
#    {'time': '2022-03-01 23:48:39', 'msg': 'Static Test Message #1', 'id': 1646174919000},
#    {'time': '2022-03-01 23:52:51', 'msg': 'Static Test Message #2', 'id': 1646175171000},
#    {'time': '2022-03-01 23:52:53', 'msg': 'Static Test Message #3', 'id': 1646175173000},
# ]

MESSAGE_STORE = []
SERVER_IDENTITIES = {}

MESSAGE_BUFFER_SIZE = 20
DEBUG = False

APP_NAME = "nexus"
NEXUS_SERVER_ADDRESS = ('', 4281)
NEXUS_SERVER_ASPECT = "deltamatrix"
NEXUS_SERVER_IDENTITY = None
NEXUS_SERVER_TIMEOUT = 5


def initialize_server(configpath, server_port=None, server_apspect=None):
    global NEXUS_SERVER_ADDRESS
    global NEXUS_SERVER_ASPECT
    global NEXUS_SERVER_IDENTITY

    # Pull up Reticulum stack as configured
    RNS.Reticulum(configpath)

    # Set default server port if not specified otherwise
    if server_port is not None:
        NEXUS_SERVER_ADDRESS = ('', int(server_port))

    # Set default nexus aspect if not specified otherwise
    # Announcement with that aspects are considered as message subscriptions
    if server_apspect is not None:
        NEXUS_SERVER_ASPECT = server_apspect

    # Log actually used parameters
    RNS.log(
        "Server Parameter --port:" + str(NEXUS_SERVER_ADDRESS[1]) + " --aspect:" + NEXUS_SERVER_ASPECT
    )

    # Create the identify of this server
    # Each time the server starts a new identity with new keys is created
    NEXUS_SERVER_IDENTITY = RNS.Identity()
    # Create and register this server as a Reticulum target so that other nexus server can distribute message hereto
    server_destination = RNS.Destination(
        NEXUS_SERVER_IDENTITY,
        RNS.Destination.IN,
        RNS.Destination.SINGLE,
        APP_NAME,
        NEXUS_SERVER_ASPECT
    )

    # Register a handler to process all incoming announcements with the aspect of this nexus server
    announce_handler = AnnounceHandler(
        aspect_filter=APP_NAME + '.' + NEXUS_SERVER_ASPECT
    )
    RNS.Transport.register_announce_handler(announce_handler)

    # Register a call back function to process all incoming data packages (aka messages)
    server_destination.set_packet_callback(packet_callback)

    # Announce this server to the network
    # All other nexus server with the same aspect will register this server as a distribution target
    server_destination.announce(app_data=(APP_NAME + '.' + NEXUS_SERVER_ASPECT).encode("utf-8"))

    # Launch HTTP GET/POST processing
    # This is a endless loop
    # Termination by ctrl-c or like process termination
    launch_http_server()


def launch_http_server():
    global NEXUS_SERVER_ASPECT
    global NEXUS_SERVER_ADDRESS

    # Create multithreading http server with given address and port to listen for json app interaction
    httpd = ThreadingHTTPServer(NEXUS_SERVER_ADDRESS, ServerRequestHandler)
    # Log launch with aspect and address/port used
    RNS.log(
        "serving Nexus aspect <" + NEXUS_SERVER_ASPECT + "> at %s:%d" % NEXUS_SERVER_ADDRESS
    )
    # Invoke server loop
    # (infinite)
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
        global SERVER_IDENTITIES

        # Log that we received an announcement matching our aspect filter criteria
        RNS.log(
            "Received an announce from " +
            RNS.prettyhexrep(destination_hash)
        )
        RNS.log(
            "The announce contained the following app data: " +
            app_data.decode("utf-8")
        )

        # Get dict key and timestamp for distribution identity registration
        dict_key = announced_identity.get_public_key()
        dict_time = int(time.time())

        # Add announced nexus distribution target identity to distribution dict
        SERVER_IDENTITIES[dict_key] = (dict_time, announced_identity)

        # Log list of last heard durations
        # Actually I have no clue how ti generate a proper human readable server name from that id
        # However since reticulum can obviously - I don't care actually
        for element in SERVER_IDENTITIES:
            timestamp = SERVER_IDENTITIES[element][0]
            RNS.log(
                "Registered Server last heard: " + str(int(time.time()) - timestamp) + "sec"
            )


def packet_callback(data, packet):
    # Reconstruct original python object
    # In this case it was a python dictioanry containing the json message
    message = pickle.loads(data)

    # append the JSON message map to the message store at last position
    MESSAGE_STORE.append(message)
    # Check store size if defined limit is reached
    length = len(MESSAGE_STORE)
    if length > MESSAGE_BUFFER_SIZE:
        # If limit is exceeded just drop first (oldest) element of list
        MESSAGE_STORE.pop(0)
    # Log message received by distribution event
    RNS.log(
        "Message received via Nexus Multicast: " + str(message)
    )
    # clean up
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
        self.wfile.write(json.dumps(MESSAGE_STORE).encode('utf-8'))

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
        MESSAGE_STORE.append(message)
        # Check store size if defined limit is reached
        length = len(MESSAGE_STORE)
        if length > MESSAGE_BUFFER_SIZE:
            # If limit is exceeded just drop first (oldest) element of list
            MESSAGE_STORE.pop(0)
        # Log message received event
        RNS.log(
            "Message received via HTTP POST: " + str(message)
        )

        # Loop through all registered distribution targets
        # and remove all targets that have not announced them self within given timeout period
        for element in SERVER_IDENTITIES:
            # Get time stamp from target dict
            timestamp = SERVER_IDENTITIES[element][0]
            # Get actual time from system
            actual_time = int(time.time())
            # Check if target has not expired yet
            if (actual_time - timestamp) < NEXUS_SERVER_TIMEOUT:
                # Get target identity from target dict
                announced_server = SERVER_IDENTITIES[element][1]
                # Create destination
                remote_server = RNS.Destination(
                    announced_server,
                    RNS.Destination.OUT,
                    RNS.Destination.SINGLE,
                    APP_NAME,
                    NEXUS_SERVER_ASPECT
                )
                # Send message to destination
                RNS.Packet(remote_server, pickle.dumps(message), create_receipt=False).send()
                # Log that we send something
                RNS.log(
                    "Message distributed to " + str(len(SERVER_IDENTITIES)) + " destinations"
                )
            else:
                # Remove expired target identity from distribution list
                SERVER_IDENTITIES.pop(element)
                # Log that we did so
                RNS.log(
                    "Distribution identity removed"
                )

        # DEBUG: Log actual message store to console
        if DEBUG:
            for s in MESSAGE_STORE:
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
