#!/usr/bin/env python3
# ##########################################################################################
# Nexus Message Server
#

import os
import signal
import threading
import sys
import argparse
import RNS
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from http import HTTPStatus
import requests
import json
import pickle
import time

import vendor.umsgpack as msgpack

##########################################################################################
# Global variables
#

# Server Version
__version__ = "1.3.0"

version = (1, 3, 0)
"Module version tuple"

# Trigger some Debug only related log entries
DEBUG = False

# Message storage
STORAGE_DIR = os.path.expanduser("~") + "/.nexus/storage"
# Message storage
STORAGE_FILE = STORAGE_DIR + "/messages.umsgpack"

# Message buffer used for actually server messages
MESSAGE_STORE = []
# Number of messages hold (Size of message buffer)
MESSAGE_BUFFER_SIZE = 20

# Distribution links
# List of subscribed reticulum identities and their target hashes and public keys to distribute messages to
# Entries are a lists (int, RNS.Identity ,bytes) containing a time stamp, the announced reticulum identity object and
# the destination hash.
# These lists are stored in the map by using the public key of the identity as map key.
# This key ist used to insert new entries as well as updating already existing entries (time stamp) to prevent
# subscription timeouts during announce and paket processing.
DISTRIBUTION_TARGETS = {}

# Bridge links
# These links are used to propagate messages into other nexus message server networks
# This can be used to keep announcement traffic within a small bunch of servers als well as to reduce redundant
# message traffic into the bridged cluster of servers.
# These links are use as additional distribution targets
# Links ar specified using an array of json map as startup parameter --bridge
# BRIDGE_LINKS = [
#    {'url': 'https://nexus.deltamatrix.org:8241', 'bridge': 'dev.test01'},
#    {'url': 'https://nexus.deltamatrix.org:8242', 'bridge': 'dev.test02'}
# ]
BRIDGE_TARGETS = [{}]

# Json labels used
# Message format used with client app
# Message Examples:
# {"id": Integer, "time": "String", "msg": "MessageBody"}
# {'id': 1646174919000. 'time': '2022-03-01 23:48:39', 'msg': 'Test Message #1'}
# Tags used in messages
MESSAGE_JSON_TIME = "time"
MESSAGE_JSON_MSG = "msg"
MESSAGE_JSON_ID = "id"
# Tags used with normal distribution management
MESSAGE_JSON_ORIGIN = "origin"
MESSAGE_JSON_VIA = "via"

# Tags used with bridge distribution management
BRIDGE_JSON_URL = "url"
BRIDGE_JSON_BRIDGE = "bridge"

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
# 43200sec <> 12h ; After 12h expired distribution targets are removed
NEXUS_SERVER_TIMEOUT = 43200
# Re-announce early enough that at least a second announce may reach other servers prior expiration timeout
NEXUS_SERVER_LONGPOLL = int(NEXUS_SERVER_TIMEOUT / 2.5)
# Delay of initial announcement of this server to the network
INITIAL_ANNOUNCEMENT_DELAY = 5

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
#   long_poll<str>:         Period in sec between announcements of this server
#   time_out<str>:          Period in sec until distribution link expires in case it is not updated by an announcement
#
# The parameters are parsed by __main__ and then passed to this function.
# Example call with all parameters given with their actual default values:
#
# python3 nexus_server.py --config="~/.reticulum" --port:4281 --aspect=server --role="{\"c\":\"root\"}"
#
def initialize_server(
        configpath,
        server_port=None, server_aspect=None, server_role=None, long_poll=None, time_out=None, bridge_links=None
):
    global NEXUS_SERVER_ADDRESS
    global NEXUS_SERVER_ASPECT
    global NEXUS_SERVER_IDENTITY
    global NEXUS_SERVER_DESTINATION
    global NEXUS_SERVER_ROLE
    global NEXUS_SERVER_LONGPOLL
    global NEXUS_SERVER_TIMEOUT
    global MESSAGE_STORE
    global BRIDGE_TARGETS

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

    # Time out configuration
    # Expiration of distribution link occurs after this many seconds without another announcement
    if time_out is not None:
        # Update long poll to its default value according the actual default configuration
        NEXUS_SERVER_LONGPOLL = int(float(time_out) / (NEXUS_SERVER_TIMEOUT / NEXUS_SERVER_LONGPOLL))
        # Overwrite default time out with specified value
        NEXUS_SERVER_TIMEOUT = int(time_out)

    # Long poll configuration
    # Announcement of this server is repeated after the specified seconds
    if long_poll is not None:
        # Overwrite default long poll default with specified value
        NEXUS_SERVER_LONGPOLL = int(long_poll)

    # Bridge link configuration
    # Valid server link urls as used in the client for POST/GET HTTP requests
    if bridge_links is not None:
        # Overwrite default role with specified role
        BRIDGE_TARGETS = json.loads(bridge_links)

    # Log actually used parameters
    RNS.log("Server Server v" + __version__ + " configuration:")
    RNS.log("--timeout=" + str(NEXUS_SERVER_TIMEOUT))
    RNS.log("--longpoll=" + str(NEXUS_SERVER_LONGPOLL))
    RNS.log("--port=" + str(NEXUS_SERVER_ADDRESS[1]))
    RNS.log("--aspect=" + NEXUS_SERVER_ASPECT)
    RNS.log("--role=" + str(NEXUS_SERVER_ROLE))
    RNS.log("--bridge=" + str(BRIDGE_TARGETS))

    # Load messages from storage
    # Check if storage path is available
    if not os.path.isdir(STORAGE_DIR):
        # Create storage path
        os.makedirs(STORAGE_DIR)
        # Log that storage directory was created
        RNS.log(
            "Created storage path " + STORAGE_DIR
        )
    # Check if we can read some messages from storage
    if os.path.isfile(STORAGE_FILE):
        try:
            file = open(STORAGE_FILE, "rb")
            MESSAGE_STORE = msgpack.unpackb(file.read())
            file.close()
            RNS.log(
                str(len(MESSAGE_STORE)) + " messages loaded from storage: " + STORAGE_FILE
            )
        except Exception as e:
            RNS.log("Could not load messages from " + STORAGE_FILE)
            RNS.log("The contained exception was: %s" % (str(e)))
    else:
        RNS.log("No messages to load from " + STORAGE_FILE)

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
    # Log server address
    RNS.log(
        "Server full address: " + str(NEXUS_SERVER_DESTINATION)
    )
    RNS.log(
        "Server address (hash): " + RNS.prettyhexrep(NEXUS_SERVER_DESTINATION.hash)
    )

    # Approve all packages received (no handler necessary)
    NEXUS_SERVER_DESTINATION.set_proof_strategy(RNS.Destination.PROVE_ALL)

    # Create a handler to process all incoming announcements with the aspect of this nexus server
    announce_handler = AnnounceHandler(
        aspect_filter=APP_NAME + '.' + NEXUS_SERVER_ASPECT
    )
    # Log announce filter
    RNS.log(
        "Announce filter set to: " + APP_NAME + '.' + NEXUS_SERVER_ASPECT
    )

    # Register the handler with the reticulum transport layer
    RNS.Transport.register_announce_handler(announce_handler)

    # Register a call back function to process all incoming data packages (aka messages)
    NEXUS_SERVER_DESTINATION.set_packet_callback(packet_callback)

    # Start timer to announce this server after 3 sec
    # All other nexus server with the same aspect will register this server as a distribution target
    # This function activates the longpoll re announcement loop to prevent subscription timeouts at linked servers
    # Using a 3sec delay is useful while debugging oder development since dev servers need to be listening prior
    # announcements may link them to a testing cluster or like subscription topology
    t = threading.Timer(INITIAL_ANNOUNCEMENT_DELAY, announce_server)
    # Star as daemon so it terminates with main thread
    t.daemon = True
    t.start()

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
def single_announce_server():
    global NEXUS_SERVER_DESTINATION
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


def announce_server():
    global NEXUS_SERVER_LONGPOLL

    # Announce this server to the network
    # All other nexus server with the same aspect will register this server as a distribution target
    single_announce_server()

    # Start timer to re announce this server in due time as specified
    t = threading.Timer(NEXUS_SERVER_LONGPOLL, announce_server)
    # Start as daemon so it terminates with main thread
    t.daemon = True
    t.start()


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
        "serving '" + APP_NAME + '.' + NEXUS_SERVER_ASPECT + "' at %s:%d" % NEXUS_SERVER_ADDRESS
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
# Role of Server #1: {"c":"Cluster_A"}
# Role of Server #2: {"c":"Cluster_B"}
# Role of Server #3: {"c":"Cluster_C"}
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
# Role of Server #1: {"c":"Cluster_A"}
# Role of Server #2: {"c":"Cluster_A","g":"GateWayAB"}
# Role of Server #3: {"c":"Cluster_B","g":"GateWayAB"}
# Role of Server #4: {"c":"Cluster_B"}
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
        global DISTRIBUTION_TARGETS

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
        dict_key = RNS.prettyhexrep(destination_hash)
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

            # Check if destination is a new destination
            if dict_key not in DISTRIBUTION_TARGETS.keys():
                # Destination is new
                # Announce this server once out of sequence to accelerate distribution list build up at that new
                # server destination subscription list
                single_announce_server()
                # Log that we added new subscription
                RNS.log(
                    "Subscription for " + RNS.prettyhexrep(destination_hash) +
                    " will be added"
                )
            else:
                # Log that we just updated new subscription
                RNS.log(
                    "Subscription for " + RNS.prettyhexrep(destination_hash) +
                    " will be updated"
                )
            # Register o9r update destination as valid distribution target
            DISTRIBUTION_TARGETS[dict_key] = (dict_time, announced_identity, destination_hash)

            # Log list of severs with seconds it was last heard
            for element in DISTRIBUTION_TARGETS.copy():
                # Get timestamp and destination hash from dict
                timestamp = DISTRIBUTION_TARGETS[element][0]
                destination = RNS.prettyhexrep(DISTRIBUTION_TARGETS[element][2])
                # Calculate seconds since last announce
                last_heard = int(time.time()) - timestamp

                # If destination is expired remove it from dict
                # (This check and cleanup is done at the distribution function as well)
                if last_heard >= NEXUS_SERVER_TIMEOUT:
                    # Log that we removed the destination
                    RNS.log(
                        "Distribution destination " + RNS.prettyhexrep(DISTRIBUTION_TARGETS[element][2]) + " removed"
                    )
                    # Actually remove destination from dict
                    DISTRIBUTION_TARGETS.pop(element)

                # If actual is still valid log it
                RNS.log(
                    "Registered Server " + destination + " last heard " + str(last_heard) + "sec ago."
                )
        else:
            # Announce should be ignored since it belongs to a different cluster, and we are not eligible to
            # link with that cluster as gateway too
            RNS.log(
                "Announced nexus target was ignored"
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
        "Message received via nexus multicast: " + str(message)
    )
    # Processing received  message
    process_incoming_message(message)


# Process incoming message
# This function is called by the reticulum paket handler (message was received as reticulum message) and by the POST
# request handler in case it was received from a client or bridge Post
def process_incoming_message(message):
    # Back propagation to origin suppression
    # If incoming message originated from this server suppress distributing it again
    if message[MESSAGE_JSON_ORIGIN] == RNS.prettyhexrep(NEXUS_SERVER_DESTINATION.hash):
        # Log message received by distribution event
        RNS.log(
            "Message distribution is suppressed because origin was this server."
        )
        exit()
    # Back propagation to forwarder suppression
    # If incoming message originated from this server suppress distributing it again
    if message[MESSAGE_JSON_VIA] == RNS.prettyhexrep(NEXUS_SERVER_DESTINATION.hash):
        # Log message received by distribution event
        RNS.log(
            "Message distribution is suppressed because we received it from this server."
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
            "Message is first message in the buffer"
        )
        # Append the JSON message map to the message store at last position
        MESSAGE_STORE.append(message)
        # Save messages to message store
        save_messages()
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
                        "Message storing and distribution not necessary because message is already in the buffer"
                    )
                    break
                # Message has same time stamp but differs
                else:
                    # Log message insertion with same timestamp
                    RNS.log(
                        "Message has a duplicate timestamp but differs (Message will be inserted in timeline)"
                    )
                    # Insert it at the actual position
                    MESSAGE_STORE.insert(i, message)
                    # Save messages to message store
                    save_messages()
                    # Distribute message to all registered nexus servers
                    distribute_message(message)
                    break
            # Timestamps to not mach
            # lets check if it is to be inserted here
            elif message_id < MESSAGE_STORE[i][MESSAGE_JSON_ID]:
                # Yes it is
                # Log message insertion with same timestamp
                RNS.log(
                    "Message will be inserted in timeline"
                )
                # Insert it at the actual position
                MESSAGE_STORE.insert(i, message)
                # Save messages to message store
                save_messages()
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
                    "Message is most recent and will be appended to timeline"
                )
                # Append the JSON message map to the message store at last position
                MESSAGE_STORE.append(message)
                # Save messages to message store
                save_messages()
                # Distribute message to all registered nexus servers
                distribute_message(message)
                break

    # No we are done with adding and distributing
    # Lets check store size if defined limit is reached now
    length = len(MESSAGE_STORE)
    if length > MESSAGE_BUFFER_SIZE:
        # Log message pop
        RNS.log(
            "Maximum message count of " + str(MESSAGE_BUFFER_SIZE) +
            " exceeded. Oldest message is dropped now"
        )
        # If limit is exceeded just drop first (oldest) element of list
        MESSAGE_STORE.pop(0)
        # Save messages to message store
        save_messages()

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
        # Log message received event
        RNS.log(
            "Message received via HTTP POST: " + str(message)
        )

        # Check if incoming message was a client sent message and does not have a bridge: tag
        if BRIDGE_JSON_BRIDGE not in message.keys():
            # Set origin and via destination id into message to prevent back propagation loops and necessary
            # redundant re-distribution of messages
            message[MESSAGE_JSON_ORIGIN] = RNS.prettyhexrep(NEXUS_SERVER_DESTINATION.hash)
            message[MESSAGE_JSON_VIA] = message[MESSAGE_JSON_ORIGIN]
            # Log client message event
            RNS.log(
                "Message was posted by a client app. Origin and via tags have been set to: " +
                message[MESSAGE_JSON_ORIGIN]
            )
        else:
            # Log client message event
            RNS.log(
                "Message was posted by a server bridge with: origin=" + message[MESSAGE_JSON_ORIGIN] +
                " and via=" + message[MESSAGE_JSON_ORIGIN]
            )

        # Store and distribute message as required
        process_incoming_message(message)

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
    for target in DISTRIBUTION_TARGETS.copy():
        # Get target identity from target dict
        # and create distribution destination
        remote_server = RNS.Destination(
            DISTRIBUTION_TARGETS[target][1],
            RNS.Destination.OUT,
            RNS.Destination.SINGLE,
            APP_NAME,
            NEXUS_SERVER_ASPECT
        )

        # Back propagation to origin suppression
        # If origin of message to distribute equals target suppress distributing it
        if message[MESSAGE_JSON_ORIGIN] == RNS.prettyhexrep(remote_server.hash):
            # Log message received by distribution event
            RNS.log(
                "Distribution to " + RNS.prettyhexrep(remote_server.hash) +
                " was suppressed because message originated from that server"
            )
        # Back propagation to forwarder suppression
        # If forwarder of message to distribute equals target suppress distributing it
        elif message[MESSAGE_JSON_VIA] == RNS.prettyhexrep(remote_server.hash):
            # Log message received by distribution event
            RNS.log(
                "Distribution to " + RNS.prettyhexrep(remote_server.hash) +
                " was suppressed because message was forwarded from that server"
            )
        else:
            # Get time stamp from target dict
            timestamp = DISTRIBUTION_TARGETS[target][0]
            # Get actual time from system
            actual_time = int(time.time())
            # Check if target has not expired yet
            if (actual_time - timestamp) < NEXUS_SERVER_TIMEOUT:
                # Set new forwarder (VIA) id to message
                message[MESSAGE_JSON_VIA] = RNS.prettyhexrep(NEXUS_SERVER_DESTINATION.hash)
                # Send message to destination
                RNS.Packet(remote_server, pickle.dumps(message), create_receipt=False).send()
                # Log that we send something to this destination
                RNS.log(
                    "Message sent to destination " + RNS.prettyhexrep(DISTRIBUTION_TARGETS[target][2])
                )
            else:
                # Log that we removed the destination
                RNS.log(
                    "Distribution destination " + RNS.prettyhexrep(DISTRIBUTION_TARGETS[target][2]) + " removed"
                )
                # Remove expired target identity from distribution list
                DISTRIBUTION_TARGETS.pop(target)

    # Loop through all registered bridge targets
    # and remove all targets that have not announced them self within given timeout period
    # If one target is not expired send message to that target
    for bridge_target in BRIDGE_TARGETS:
        # Use POST to send message to bridge nexus server link
        result = requests.post(bridge_target[BRIDGE_JSON_URL], message)
        # Log that we bridged a message
        RNS.log("Bridge POST to " + bridge_target[BRIDGE_JSON_URL])
        RNS.log("Bridge POST result was " + result.text)

# url = 'https://nexus.deltamatrix.org:8244'
# myobj = {'somekey': 'somevalue'}
# x = requests.post(url, data = myobj)
# print(x.text)
# https://nexus.deltamatrix.org:8244


##########################################################################################
# Save messages to storage file
#
def save_messages():
    global MESSAGE_STORE

    # Check if storage file is there
    try:
        save_file = open(STORAGE_FILE, "wb")
        save_file.write(msgpack.packb(MESSAGE_STORE))
        save_file.close()
        RNS.log("Messages saved to storage file:" + STORAGE_FILE)

    except Exception as err:
        RNS.log("Could not save message to storage file: " + STORAGE_FILE)
        RNS.log("The contained exception was: %s" % (str(err)), RNS.LOG_ERROR)


#######################################################
# Program Startup
#
# Default python entrypoint with processing the give commandline parameters
#

def signal_handler(_signal, _frame):
    print("exiting")
    sys.exit(0)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)

    # Parse commandline arguments
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

        parser.add_argument(
            "--longpoll",
            action="store",
            default=None,
            help="time in seconds between recurring announcements",
            type=str
        )

        parser.add_argument(
            "--timeout",
            action="store",
            default=None,
            help="time in seconds until distribution registration expires",
            type=str
        )

        parser.add_argument(
            "--bridge",
            action="store",
            default=None,
            help="list of maps containing bridge link connection data",
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

        if params.longpoll:
            longpoll_para = params.longpoll
        else:
            longpoll_para = None

        if params.timeout:
            timeout_para = params.timeout
        else:
            timeout_para = None

        if params.bridge:
            bridge_para = params.bridge
        else:
            bridge_para = None

        # Call server initialization and startup reticulum and HTTP listeners
        initialize_server(config_para, port_para, aspect_para, role_para, longpoll_para, timeout_para, bridge_para)

    # Handle keyboard interrupt aka ctrl-C to exit server
    except KeyboardInterrupt:
        print("Server terminated by ctrl-c")
        sys.exit(0)
