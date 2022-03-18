##########################################################################################
# Nexus Message Server
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

##########################################################################################
# Global variables
#

# Trigger some Debug only related log entries
DEBUG = True

# This are the data stores used by the server
# ToDo: Implement data persistence on restart
#           ORM
#           Persistence Layer for
#              SQLLight
#              PostgresQL
#
# Message buffer used for actually server messages
MESSAGE_STORE = []
# Number of messages hold (Size of message buffer)
MESSAGE_BUFFER_SIZE = 20

# List of subscribed reticulum identities and their target hashes and public keys to distribute messages to
# Entries are a lists (int, RNS.Identity ,bytes) containing a time stamp, the announced reticulum identity object and
# the destination hash.
# These lists are stored in the map by using the public key of the identity as map key.
# This key ist used to insert new entries as well as updating already existing entries (time stamp) to prevent
# subscription timeouts during announce and paket processing.
SERVER_IDENTITIES = {}

# Json labels used
# Message format used with client app
# Message Examples:
# {"id": Integer, "time": "String", "msg": "MessageBody"}
# {'id': 1646174919000. 'time': '2022-03-01 23:48:39', 'msg': 'Test Message #1'}
MESSAGE_JSON_TIME = "time"
MESSAGE_JSON_MSG = "msg"
MESSAGE_JSON_ID = "id"
MESSAGE_JSON_ORIGIN = "origin"

# Server to server protokoll used for automatic subscription (Cluster and Gateway)
# Role Example: {"c": "ClusterName", "g": "GatewayName"}
ROLE_JSON_CLUSTER = "c"
ROLE_JSON_GATEWAY = "g"

# Some Server default values used to announce nexus servers to reticulum
APP_NAME = "nexus"
NEXUS_SERVER_ASPECT = "server"

# Default server cluster that is announced to be subscribed to
# This one can be used to run not connected server names by just giving all servers different cluster names
# These servers can later be interconnected by using gateway names (see server role)
DEFAULT_CLUSTER = "root"
# The server role has two parts. 'cluster' and 'gateway'. By default, only cluster is used and preset by the global
# variable above. # If gateway is set as well other nexus server can auto subscribe by announcing the same cluster
# or same gateway name with their json role specification.
NEXUS_SERVER_ROLE = {ROLE_JSON_CLUSTER: DEFAULT_CLUSTER}

# Some Server default values used to announce server to reticulum
NEXUS_SERVER_ADDRESS = ('', 4281)

# Timeout constants for automatic subscription handling
# 3600sec <> 12h ; After 12h expired distribution targets are removed
NEXUS_SERVER_TIMEOUT = 3600
# Re-announce after half the expiration time
# NEXUS_SERVER_LONGPOLL = NEXUS_SERVER_TIMEOUT / 2
NEXUS_SERVER_LONGPOLL = 15

# Global Reticulum Instances to be used by server functions
# The reticulum target of this server
NEXUS_SERVER_DESTINATION = RNS.Destination
# The identity use by this server
NEXUS_SERVER_IDENTITY = RNS.Identity


##########################################################################################
# Initialize Nexus Server
# Parameters:
#   configpath<str>:        Alternate config path to be used for initialization of reticulum
#   server_port<str>:       HTTP port to listen for POST/GET client app requests
#   server_aspect<str>:     Reticulum target aspect to filter announces along with app name like
#                           <app_name>.<server_aspect>
#   server_role<jsonStr>:   Nexus Server role specification to specify automatic subscription handling
#                           e.g. {"c":"cluster","g":"gateway"}
#
# The parameters are parsed by __main__ and then passed to this function.
# Example call with all parameters given with their actual default values:
#
# python3 nexus_server.py --config="~/.reticulum" --port:4281 --aspect=server --role="{\"c\":\"root\"}"
#
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
    # Announcement with that aspects are evaluated for possible automatic subscription
    if server_aspect is not None:
        # Overwrite default aspect
        NEXUS_SERVER_ASPECT = server_aspect

    # Role configuration of the server
    # Announcement with similar cluster oder gateway names are considered as message subscriptions
    if server_role is not None:
        # Overwrite default role with specified role
        NEXUS_SERVER_ROLE = json.loads(server_role)

    # Log actually used parameters
    RNS.log(
        "Server configuration set up:" +
        " port=" + str(NEXUS_SERVER_ADDRESS[1]) +
        " aspect=" + NEXUS_SERVER_ASPECT +
        " role=" + str(NEXUS_SERVER_ROLE)
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


##########################################################################################
# Announce the server to the reticulum network
#
# Calling this function will start a timer that will call this function again after the
# specified re-announce period.
#
def announce_server():
    global NEXUS_SERVER_DESTINATION
    global NEXUS_SERVER_ASPECT
    global APP_NAME
    global NEXUS_SERVER_LONGPOLL
    global NEXUS_SERVER_ROLE

    # Announce this server to the network
    # All other nexus server with the same aspect will register this server as a distribution target
    # noinspection PyArgumentList
    NEXUS_SERVER_DESTINATION.announce(
        # Serialize the nexus server role dict to bytes and set it as app_date to the announcement
        app_data=pickle.dumps(NEXUS_SERVER_ROLE)
    )
    # Log announcement / long poll announcement
    RNS.log(
        # Log entry does not use bytes but a string representation
        "Server announce sent with app_data: " + str(NEXUS_SERVER_ROLE)
    )

    # Start timer to re announce this server in due time as specified
    threading.Timer(NEXUS_SERVER_LONGPOLL, announce_server).start()


##########################################################################################
# Start up of the threaded HTTP server to handle client json GET/POST requests
#
def launch_http_server():
    global NEXUS_SERVER_ASPECT
    global NEXUS_SERVER_ADDRESS

    # Create multithreading http server with given address and port to listen for json app interaction
    httpd = ThreadingHTTPServer(NEXUS_SERVER_ADDRESS, ServerRequestHandler)
    # Log launch with aspect and address/port used
    RNS.log(
        "serving Nexus aspect '" + NEXUS_SERVER_ASPECT + "' at %s:%d" % NEXUS_SERVER_ADDRESS
    )
    # Invoke server loop
    # (infinite)
    httpd.serve_forever()


##########################################################################################
# Reticulum handler class to process received announces
#
# This handler will be called as soon as an announcement of another nexus server was received.
# Nexus servers are recognized by setting their app_name and aspect to the same values.
# The app data received with the announcement is considered as a serialized json map containing the role
# specification of the remote server having twi parts:
#
# - Cluster specification
# - Gateway specification
#
# A nexus server can automatically connect with other nexus server using the same cluster name effectively forming
# an n:m redundant server cluster that exchange and mirror all messages received within the cluster.
# This is simply achieved by specifying the same cluster name inside the nexus server role that is appended to the
# reticulum target announcement.
# Using e.g. {"c":"MyCluster"} as the nexus server role of 3 distinct servers anywhere at the reticulum network will
# trigger an automatic subscription and message forwarding mechanism that provides for having new messages mirrored
# to all serves in that cluster.
# Nexus servers using different cluster name will not automatically subscribe to each other thus being standalone
# servers or separate clusters.
#
# The Gateway names specified at the server role acts identical to the cluster name in a way that an automatic
# subscription ist triggered if the received announcement contained a nexus server role with has a cluster name that
# matches the cluster name of the actual server OR the gateway name matches the gateway name of the actual server.
# This establishes a second layer to create automatic connections. These can be used to daisy chain nexus servers
# without any redundancy or to connect one cluster to another cluster.
#
# Role configuration example for three separate standalone nexus servers:
# Role of Server #1: {"c":"Server_A"}
# Role of Server #2: {"c":"Server_B"}
# Role of Server #3: {"c":"Server_C"}
#
# Role configuration example for a single redundant nexus server cluster consisting of three servers:
# Role of Server #1: {"c":"Cluster_A"}
# Role of Server #2: {"c":"Cluster_A"}
# Role of Server #3: {"c":"Cluster_A"}
#
# Role configuration example for two redundant but not connected nexus server clusters consisting of three servers each:
# Role of Server #1: {"c":"Cluster_A"}
# Role of Server #2: {"c":"Cluster_A"}
# Role of Server #3: {"c":"Cluster_A"}
# Role of Server #4: {"c":"Cluster_B"}
# Role of Server #5: {"c":"Cluster_B"}
# Role of Server #6: {"c":"Cluster_B"}
#
# Role configuration example of four redundant but daisy-chained nexus servers (less traffic than with a cluster):
# Role of Server #1: {"c":"Server_A","g":"Server_B"}
# Role of Server #2: {"c":"Server_B","g":"Server_C"}
# Role of Server #3: {"c":"Server_C","g":"Server_D"}
# Role of Server #4: {"c":"Server_D","g":"Server_C"}
#
# Role configuration example for two redundant and connected nexus server clusters consisting of three servers each and
# having one of those servers acting as a forwarding gateway to the other cluster:
# Role of Server #1: {"c":"Cluster_A"}
# Role of Server #2: {"c":"Cluster_A"}
# Role of Server #3: {"c":"Cluster_A","g":"GateWayAB"}}
# Role of Server #4: {"c":"Cluster_B","g":"GateWayAB"}}
# Role of Server #5: {"c":"Cluster_B"}
# Role of Server #6: {"c":"Cluster_B"}
#
# To have this automatic subscription mechanism available effectively provides for having a deterministic client server
# network with automatic replication on top of the Reticulum mesh network.
#
# During announcement processing all expired distribution targets (cluster and gateway links) are dropped.
# All linked nexus servers that have updated their availability by an re-announcement prior the expiration period will
# be kept as valid distribution targets.
#
class AnnounceHandler:
    global NEXUS_SERVER_ROLE

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
    @staticmethod
    def received_announce(destination_hash, announced_identity, app_data):
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

        # Add announced nexus distribution target to distribution dict if it has the same cluster or gateway name.
        # This is to enable that servers of the actual cluster are subscribed for distribution as well as serves
        # that announce themselves with a secondary cluster aka gateway cluster name.

        # Check if we have cluster match
        # with check if key is at both maps
        link_flag1 = (ROLE_JSON_CLUSTER in NEXUS_SERVER_ROLE and ROLE_JSON_CLUSTER in announced_role)
        if link_flag1:
            link_flag1 = NEXUS_SERVER_ROLE[ROLE_JSON_CLUSTER] == announced_role[ROLE_JSON_CLUSTER]
        # Check if we have gateway match
        # with check if key is at both maps
        link_flag2 = (ROLE_JSON_GATEWAY in NEXUS_SERVER_ROLE and ROLE_JSON_GATEWAY in announced_role)
        if link_flag2:
            link_flag2 = NEXUS_SERVER_ROLE[ROLE_JSON_GATEWAY] == announced_role[ROLE_JSON_GATEWAY]

        # If we had a cluster or gateway match subscribe announced target
        if link_flag1 or link_flag2:
            # Register destination as valid distribution target
            SERVER_IDENTITIES[dict_key] = (dict_time, announced_identity, destination_hash)
            # If actual is still valid log it
            RNS.log(
                "Subscription for " + RNS.prettyhexrep(destination_hash) +
                " was added/updated"
            )
            # Log list of severs with seconds it was last heard
            for element in SERVER_IDENTITIES.copy():
                # Get timestamp and destination hash from dict
                timestamp = SERVER_IDENTITIES[element][0]
                destination = RNS.prettyhexrep(SERVER_IDENTITIES[element][2])
                # Calculate seconds since last announce
                last_heard = int(time.time()) - timestamp

                # If destination is expired remove it from dict
                # (This check and cleanup is done at the distribution function as well)
                if last_heard >= NEXUS_SERVER_TIMEOUT:
                    # Log that we removed the destination
                    RNS.log(
                        "Distribution destination " + RNS.prettyhexrep(SERVER_IDENTITIES[element][2]) + " removed"
                    )
                    # Actually remove destination from dict
                    SERVER_IDENTITIES.pop(element)

                # If actual is still valid log it
                RNS.log(
                    "Registered Server " + destination + " last heard " + str(last_heard) + "sec ago."
                )
        else:
            # Announce should be ignored since it belongs to a different cluster, and we are not eligible to
            # link with that cluster as gateway too
            RNS.log(
                "Announced Nexus target was ignored"
            )


##########################################################################################
# Reticulum callback to handle incoming data packets
#
# This function is called as soon as a data packet is received by this server target
# Actually all packets are treated as messages.
# ToDo: Implement server commands
#           Digest message
#           Remove message
#           Get messages (since)
#           Get last messages (number of messages)
#
def packet_callback(data, _packet):
    # Reconstruct original python object
    # In this case it was a python dictionary containing the json message
    message = pickle.loads(data)

    # Log message received by distribution event
    RNS.log(
        "Message received via Nexus Multicast: " + str(message)
    )

    # Back propagation suppression
    # If incoming message originated from this server suppress distributing it again
    if message[MESSAGE_JSON_ORIGIN] == str(NEXUS_SERVER_DESTINATION):
        # Log message received by distribution event
        RNS.log(
            "Message distribution is suppressed because origin was this server."
        )
        exit()

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
            "Maximum message count exceeded. Oldest message is dropped now. " + str(MESSAGE_STORE[0])
        )
        # If limit is exceeded just drop first (oldest) element of list
        MESSAGE_STORE.pop(0)

    # clean up
    sys.stdout.flush()


##########################################################################################
# HTTP request handler class to process received HTTP POST/GET app client requests
#
# The client app uses json requests to communicate with the server.
# Actually this protocol is plain simple.
#
# To send a new message to the server the client issues a POST request without any URL parameters # to the root of the
# with the message json past in the POST body.
# During POST processing the message is amended by a timestamp that ist used by the server to uniquely identify each
# message processed through message distribution and assurance of timeline accuracy. The message send from the client
# may contain any number of map members the client may send. The answer to the GET request will deliver all message map
# members originally sent from the clients as well as the amended server timestamp back to the client.
# To get the entire content of the message buffer of the server, the client issues a GET request without any URL
# parameters or body content. The answers from the server is a json list containing all messages as json maps.
#
# Example POST Body (Actual client v1.1.0 behaviour):
# {'time': '2022-03-01 23:48:39', 'msg': 'Static Test Message #1'}
#
# Example GET Response:
# [
#    {'time': '2022-03-01 23:48:39', 'msg': 'Static Test Message #1', 'id': 1646174919000},
#    {'time': '2022-03-01 23:52:51', 'msg': 'Static Test Message #2', 'id': 1646175171000},
#    {'time': '2022-03-01 23:52:53', 'msg': 'Static Test Message #3', 'id': 1646175173000},
# ]
#
class ServerRequestHandler(BaseHTTPRequestHandler):

    # Borrowing from https://gist.github.com/nitaku/10d0662536f37a087e1b
    # Set headers of actual request
    def _set_headers(self):
        # Set response result code and data format
        self.send_response(HTTPStatus.OK)
        self.send_header('Content-type', 'application/json')
        # Allow requests from any origin, so CORS policies don't
        # prevent local development.
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

    # Simple GET request handler without any URL parameters or request body processing
    # The actual message buffer list is serialized as json string and encoded as bytes.
    # After that it is sent back to the client as the GET request response.
    def do_GET(self):
        self._set_headers()
        self.wfile.write(json.dumps(MESSAGE_STORE).encode('utf-8'))

    # Simple POST request handler without any URL parameters and the message to be digested as request body
    # The actual message is decoded into a python map, amended by a timestamp and added to the message store.
    # After that it is sent back to the client as the GET request response.
    def do_POST(self):
        global MESSAGE_STORE
        # ToDo: Need to implement more features:
        #    ClearBuffer command
        #    Delete Message command
        #
        # Get length of POST message, read those bytes and parse it as JSON string into a message
        # and append that string to the message store
        length = int(self.headers.get('content-length'))
        message = json.loads(self.rfile.read(length))

        # Create a timestamp and add that to the message map
        message[MESSAGE_JSON_ID] = int(time.time() * 100000)
        # Add these servers' destination hash as origin to the message
        message[MESSAGE_JSON_ORIGIN] = str(NEXUS_SERVER_DESTINATION)
        # Log message received event
        RNS.log(
            "Message received via HTTP POST: " + str(message)
        )

        # Distribute message to all registered nexus server
        # Logging of this is done by the distribution function
        # Suppression of back propagation not necessary, since POST creates a new message
        # that needs to be sent to all active distribution targets
        distribute_message(message)

        # Append the JSON message map to the message store at last (most recent) position
        MESSAGE_STORE.append(message)
        # Check store size if defined limit is reached
        length = len(MESSAGE_STORE)
        if length > MESSAGE_BUFFER_SIZE:
            # If limit is exceeded just drop first (oldest) element of list
            MESSAGE_STORE.pop(0)
            # Log Message drop because of buffer overflow
            RNS.log(
                "Oldest message in buffer was dropped because of buffer limit of " +
                str(MESSAGE_BUFFER_SIZE) +
                " was reached."
            )

        # DEBUG: Log actual messages stored to console
        if DEBUG:
            for s in MESSAGE_STORE:
                print(s)

        # Build and return JSON success response
        self._set_headers()
        self.wfile.write(json.dumps({'success': True}).encode('utf-8'))

    # Set request options
    def do_OPTIONS(self):
        # Send allow-origin header and clearance for GET and POST requests
        self.send_response(HTTPStatus.NO_CONTENT)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST')
        self.send_header('Access-Control-Allow-Headers', 'content-type')
        self.end_headers()


##########################################################################################
# Message distribution to registered nexus serves
#
# The given message (json map) will be distributed to all linked nexus servers that have
# updated their availability by a re-announcement prior the expiration period.
# While we iterate through the list all already expired targets are dropped from the list.
# Same expiration management is done during announcement processing.
#
def distribute_message(message):
    # Loop through all registered distribution targets
    # and remove all targets that have not announced them self within given timeout period
    # If one target is not expired send message to that target
    for element in SERVER_IDENTITIES.copy():
        # Get target identity from target dict
        # and create distribution destination
        remote_server = RNS.Destination(
            SERVER_IDENTITIES[element][1],
            RNS.Destination.OUT,
            RNS.Destination.SINGLE,
            APP_NAME,
            NEXUS_SERVER_ASPECT
        )

        # Back propagation suppression
        # If origin of message to distribute equals target suppress distributing it
        if message[MESSAGE_JSON_ORIGIN] == str(remote_server):
            # Log message received by distribution event
            RNS.log(
                "Message distribution is suppressed because massage origin equals destination " +
                str(remote_server)
            )
        else:
            # Get time stamp from target dict
            timestamp = SERVER_IDENTITIES[element][0]
            # Get actual time from system
            actual_time = int(time.time())
            # Check if target has not expired yet
            if (actual_time - timestamp) < NEXUS_SERVER_TIMEOUT:
                # Send message to destination
                RNS.Packet(remote_server, pickle.dumps(message), create_receipt=False).send()
                # Log that we send something t this destination
                RNS.log(
                    "Message sent to destination " + RNS.prettyhexrep(SERVER_IDENTITIES[element][2])
                )
            else:
                # Log that we removed the destination
                RNS.log(
                    "Distribution destination " + RNS.prettyhexrep(SERVER_IDENTITIES[element][2]) + " removed"
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
# Default python entrypoint with processing the give commandline parameters
#
if __name__ == "__main__":
    try:
        parser = argparse.ArgumentParser(
            description="Minimal Nexus Message Server with automatic cluster replication"
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

        # Parse passed commandline arguments as specified above
        params = parser.parse_args()

        # Default handling of parameters is done in server initialization
        # Here all parameters not specified are set to None
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

        # Call server initialization and startup reticulum and HTTP listeners
        initialize_server(config_para, port_para, aspect_para, role_para)

    # Handle keyboard interrupt aka ctrl-C to exit server
    except KeyboardInterrupt:
        print("")
        exit()
