##########################################################################################
#
# Nexus Message Server
#
#

import sys
import argparse
import RNS
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from http import HTTPStatus
import json
import pickle
import time
import threading

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

MESSAGE_JSON_TIME = "time"
MESSAGE_JSON_MSG = "msg"
MESSAGE_JSON_ID = "id"
ROLE_JSON_CLUSTER = "cluster"
ROLE_JSON_GATEWAY = "gate"
DEFAULT_CLUSTER = "hesse"
DEFAULT_GATEWAY = "link"

APP_NAME = "nexus"
NEXUS_SERVER_ASPECT = "deltamatrix"
NEXUS_SERVER_ADDRESS = ('', 4281)

NEXUS_SERVER_TIMEOUT = 3600  # 3600sec <> 12h ; After 12h expired distribution targets are removed
NEXUS_SERVER_LONGPOLL = NEXUS_SERVER_TIMEOUT / 2  # Re-announce after half the expiration time
# NEXUS_SERVER_TIMEOUT = 10
# NEXUS_SERVER_LONGPOLL = 600

NEXUS_SERVER_ROLE = {ROLE_JSON_CLUSTER: DEFAULT_CLUSTER, ROLE_JSON_GATEWAY: DEFAULT_GATEWAY}
NEXUS_SERVER_DESTINATION = RNS.Destination
NEXUS_SERVER_IDENTITY = RNS.Identity


def initialize_server(configpath, server_port=None, server_aspect=None, server_role=None):
    global NEXUS_SERVER_ADDRESS
    global NEXUS_SERVER_ASPECT
    global NEXUS_SERVER_IDENTITY
    global NEXUS_SERVER_DESTINATION
    global NEXUS_SERVER_ROLE

    # Pull up Reticulum stack as configured
    RNS.Reticulum(configpath)

    # Set default server port if not specified otherwise
    if server_port is not None:
        NEXUS_SERVER_ADDRESS = ('', int(server_port))

    # Set default nexus aspect if not specified otherwise
    # Announcement with that aspects are considered as message subscriptions
    if server_aspect is not None:
        NEXUS_SERVER_ASPECT = server_aspect

    # Role configuration of the server
    # Announcement with that aspects are considered as message subscriptions
    if server_role is not None:
        NEXUS_SERVER_ROLE = json.loads(server_role)

    # Log actually used parameters
    RNS.log(
        "Server Parameter --port:" + str(NEXUS_SERVER_ADDRESS[1]) + " --aspect:" + NEXUS_SERVER_ASPECT
    )

    # Create the identity of this server
    # Each time the server starts a new identity with new keys is created
    NEXUS_SERVER_IDENTITY = RNS.Identity()
    # Create and register this server as a Reticulum target so that other nexus server can distribute message hereto
    NEXUS_SERVER_DESTINATION = RNS.Destination(
        NEXUS_SERVER_IDENTITY,
        RNS.Destination.IN,
        RNS.Destination.SINGLE,
        APP_NAME,
        NEXUS_SERVER_ASPECT
    )
    # Approve all packages received (no handler necessary)
    NEXUS_SERVER_DESTINATION.set_proof_strategy(RNS.Destination.PROVE_ALL)

    # Create a handler to process all incoming announcements with the aspect of this nexus server
    announce_handler = AnnounceHandler(
        aspect_filter=APP_NAME + '.' + NEXUS_SERVER_ASPECT
    )
    # Register the handler with the reticulum transport layer
    RNS.Transport.register_announce_handler(announce_handler)

    # Register a call back function to process all incoming data packages (aka messages)
    NEXUS_SERVER_DESTINATION.set_packet_callback(packet_callback)

    # Announce this server to the network
    # All other nexus server with the same aspect will register this server as a distribution target
    # This function activates the longpoll re announcement loop to prevent subscription timeouts at linked servers
    announce_server()

    t = threading.Timer(30.0, announce_server)
    t.start()  # after 30 seconds, "hello, world" will be printed

    # Launch HTTP GET/POST processing
    # This is an endless loop
    # Termination by ctrl-c or like process termination
    launch_http_server()


def announce_server():
    global NEXUS_SERVER_DESTINATION
    global NEXUS_SERVER_ASPECT
    global APP_NAME
    global NEXUS_SERVER_LONGPOLL
    global NEXUS_SERVER_ROLE

    # Announce this server to the network
    # All other nexus server with the same aspect will register this server as a distribution target
    NEXUS_SERVER_DESTINATION.announce(
        #   app_data=(APP_NAME + '.').encode("utf-8") + pickle.dumps(NEXUS_SERVER_ROLE)
        app_data=pickle.dumps(NEXUS_SERVER_ROLE)
    )
    # Log announcement / long poll announcement
    RNS.log(
        #   "Server announce sent with app_data " + APP_NAME + '.' + str(NEXUS_SERVER_ROLE)
        "Server announce sent with app_data: "+ str(NEXUS_SERVER_ROLE)
    )

    # Start timer to re announce this server in due time as specified
    threading.Timer(NEXUS_SERVER_LONGPOLL, announce_server).start()


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

        # Recreate nexus role dict from received app data
        announced_role = pickle.loads(app_data)
        # Log role
        RNS.log(
            "The announce contained the following nexus role dict: " +
            str(announced_role)
        )

        # Get dict key and timestamp for distribution identity registration
        dict_key = announced_identity.get_public_key()
        dict_time = int(time.time())

        # Add announced nexus distribution target identity to distribution dict
        SERVER_IDENTITIES[dict_key] = (dict_time, announced_identity, destination_hash)

        # Log list of last heard durations
        # Actually I have no clue how ti generate a proper human-readable server name from that id
        # However since reticulum can obviously - I don't care actually
        for element in SERVER_IDENTITIES:
            timestamp = SERVER_IDENTITIES[element][0]
            destination = str(SERVER_IDENTITIES[element][2])
            RNS.log(
                "Registered Server <" + destination + "> last heard: " + str(int(time.time()) - timestamp) + "sec"
            )


def packet_callback(data, packet):
    # Reconstruct original python object
    # In this case it was a python dictionary containing the json message
    message = pickle.loads(data)

    # Log message received by distribution event
    RNS.log(
        "Message received via Nexus Multicast: " + str(message)
    )

    # If message is more recent than the oldest message in the buffer
    # and has not arrived earlier than add/insert message at the correct position and
    # distribute the message to all registered servers

    # Get actual timestamp from message
    message_id = message[MESSAGE_JSON_ID]
    # Get actual number of messages in the buffer
    message_store_size = len(MESSAGE_STORE)

    if message_store_size == 0:
        # First message arrived event
        RNS.log(
            "Message is first message and will be appended " +
            str(message)
        )
        # Append the JSON message map to the message store at last position
        MESSAGE_STORE.append(message)
        # Distribute message to all registered nexus servers
        distribute_message(message)
    else:
        # At least one message is already there and need to be checked for insertion and distribution
        # loop through all messages and check if we have to store and distribute it
        for i in range(0, message_store_size):
            # Check if we already have that message at the actual buffer position
            if message_id == MESSAGE_STORE[i][MESSAGE_JSON_ID]:
                # Timestamp did match now check if message does too
                if message[MESSAGE_JSON_MSG] == MESSAGE_STORE[i][MESSAGE_JSON_MSG]:
                    # Log that we have that one already
                    RNS.log(
                        "Message storing and distribution not necessary 'cause message already in buffer) " +
                        str(message)
                    )
                    break
                # Message has same time stamp but differs
                else:
                    # Log message insertion with same timestamp
                    RNS.log(
                        "Message has a duplicate timestamp but differs (Message will be inserted in timeline): " +
                        str(message)
                    )
                    # Insert it at the actual position
                    MESSAGE_STORE.insert(i, message)
                    # Distribute message to all registered nexus servers
                    distribute_message(message)
                    break
            # Timestamps to not mach
            # lets check if it is to be inserted here
            elif message_id < MESSAGE_STORE[i][MESSAGE_JSON_ID]:
                # Yes it is
                # Log message insertion with same timestamp
                RNS.log(
                    "Message will be inserted in timeline): " + str(message)
                )
                # Insert it at the actual position
                MESSAGE_STORE.insert(i, message)
                # Distribute message to all registered nexus servers
                distribute_message(message)
                break
            # Continue until we find the place to insert it, or
            # we have checked the latest entry in the buffer (i=size-1)
            # If we are there than we can append and distribute it
            # After that has happened we terminate the loop as well
            # The loop will never be terminated automatically
            if i == message_store_size - 1:
                # Log message append
                RNS.log(
                    "Message is most recent and will be appended to timeline): " + str(message)
                )
                # Append the JSON message map to the message store at last position
                MESSAGE_STORE.append(message)
                # Distribute message to all registered nexus servers
                distribute_message(message)
                break

    # No we are done with adding and distributing
    # Lets check store size if defined limit is reached now
    length = len(MESSAGE_STORE)
    if length > MESSAGE_BUFFER_SIZE:
        # Log message pop
        RNS.log(
            "Maximum Message count exceeded. Oldest message is dropped now. " + str(MESSAGE_STORE[0])
        )
        # If limit is exceeded just drop first (oldest) element of list
        MESSAGE_STORE.pop(0)

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
        message[MESSAGE_JSON_ID] = int(time.time() * 100000)

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

        # Distribute message to all registered nexus server
        distribute_message(message)

        # DEBUG: Log actual message store to console
        if DEBUG:
            for s in MESSAGE_STORE:
                print(s)

        # Build and return JSON success response
        self._set_headers()
        self.wfile.write(json.dumps({'success': True}).encode('utf-8'))

    def do_OPTIONS(self):
        # Send allow-origin header and clearance for GET and POST requests
        self.send_response(HTTPStatus.NO_CONTENT)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST')
        self.send_header('Access-Control-Allow-Headers', 'content-type')
        self.end_headers()


def distribute_message(message):
    # Loop through all registered distribution targets
    # and remove all targets that have not announced them self within given timeout period
    # If one target is not expired send message to that target
    for element in SERVER_IDENTITIES.copy():
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
            # Log that we send something t this destination
            RNS.log(
                "Message sent to destination <" + str(SERVER_IDENTITIES[element][2]) + ">"
            )
        else:
            # Log that we removed the destination
            RNS.log(
                "Distribution identity of destination <" + str(SERVER_IDENTITIES[element][2]) + "> removed"
            )
            # Remove expired target identity from distribution list
            SERVER_IDENTITIES.pop(element)

        # Log number of target message was distributed to
        RNS.log(
            "Message distributed to " + str(len(SERVER_IDENTITIES)) + " destinations"
        )


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
            help="reticulum aspect to configer nexus server aspect",
            type=str
        )

        parser.add_argument(
            "--role",
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

        if params.role:
            role_para = params.role
        else:
            role_para = None

        initialize_server(config_para, port_para, aspect_para, role_para)

    except KeyboardInterrupt:
        print("")
        exit()
