#!/usr/bin/env python3
# ##########################################################################################
#
# Nexus Message Server
#
import copy
import os
import signal
import threading
import sys
import argparse

import LXMF
import RNS
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from http import HTTPStatus
import requests
import json
import pickle
import time
import string

import vendor.umsgpack as msgpack

##########################################################################################
# Global variables
#

# Server Version
__version__ = "1.3.0.3"

# Message purge version
# Increase this number to cause an automatic message drop from saved buffers or any incoming message.
# New messages will be tagged with 'v': __message_version__
__message_version__ = "3"

# Trigger some Debug only related log entries
DEBUG = False

# Message storage
MESSAGE_STORAGE_PATH = os.path.expanduser("~") + "/.nexus/storage"
MESSAGE_STORAGE_FILE = MESSAGE_STORAGE_PATH + "/messages.umsgpack"

# LXMF storage
LXMF_STORAGE_PATH = os.path.expanduser("~") + "/.nexus/lxmf"

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
#    {'url': 'https://nexus.deltamatrix.org:8241', 'tag': 'dev.test01'},
#    {'url': 'https://nexus.deltamatrix.org:8242', 'tag': 'dev.test02'}
# ]
BRIDGE_TARGETS = []

# Json labels used
# Message format used with client app
# Message Examples:
# {"id": Integer, "time": "String", "msg": "MessageBody"}
# {'id': 1646174919000. 'time': '2022-03-01 23:48:39', 'msg': 'Test Message #1'}
# Tags and constants used in messages
MESSAGE_JSON_TIME = "time"
MESSAGE_JSON_MSG = "msg"
MESSAGE_JSON_ID = "id"
MESSAGE_JSON_VERSION = "v"
MESSAGE_ID_NOT_SET = 'ID_NOT_SET'
# Tags used with normal distribution management
MESSAGE_JSON_ORIGIN = "origin"
MESSAGE_JSON_VIA = "via"
MESSAGE_JSON_ORIGIN_LOCAL = "local"
# Tags used with bridge distribution management
MESSAGE_JSON_PATH = "path"
MESSAGE_PATH_SEP = ":"
# Tags used with bridge destination management
BRIDGE_JSON_URL = "url"
BRIDGE_JSON_CLUSTER = "cluster"
# Tags used during message buffer merge (tag to indicate is selected for distribution)
MERGE_JSON_TAG = "tag"

# Server to server protokoll used for automatic subscription (Cluster and Gateway)
# The LXM Destination is added with the LXM socket instantiation
# Role Example: {'c':'ClusterName','g':'GatewayName','m':destination_hash}
ROLE_JSON_CLUSTER = "c"
ROLE_JSON_GATEWAY = "g"
ROLE_JSON_LXM_DESTINATION = "m"

# Some Server default values used to announce nexus servers to reticulum
# APP_NAME = "nexus"
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
# Nexus LXM Socket
# noinspection PyTypeChecker
NEXUS_LXM_SOCKET = None  # type: NexusLXMSocket


##########################################################################################
# Helper functions
#

##########################################################################################
# Remove all whitespaces
#
def remove_whitespace(in_string: str):
    return in_string.translate(str.maketrans(dict.fromkeys(string.whitespace)))


##########################################################################################
# Save messages to storage file
#
def save_messages():
    # Check if storage file is there
    try:
        save_file = open(MESSAGE_STORAGE_FILE, "wb")
        save_file.write(msgpack.packb(MESSAGE_STORE))
        save_file.close()
        RNS.log("Messages saved to storage file " + MESSAGE_STORAGE_FILE)

    except Exception as err:
        RNS.log("Could not save message to storage file " + MESSAGE_STORAGE_FILE)
        RNS.log("The contained exception was: %s" % (str(err)), RNS.LOG_ERROR)


##########################################################################################
# Tag message by message ID
#
def tag_message(message_id, tag, value):
    # ToDo: Refactor message storing to an array with indexed maps (possibly with DB in v2)
    for message in MESSAGE_STORE:
        if message[MESSAGE_JSON_ID] == message_id:
            message[tag] = value
            break


##########################################################################################
# Untag message by message ID
#
def untag_message(message_id, tag):
    # ToDo: Refactor message storing to an array with indexed maps (possibly with DB in v2)
    for message in MESSAGE_STORE:
        if message[MESSAGE_JSON_ID] == message_id:
            message.pop(tag)
            break


##########################################################################################
# Drop Message from message store by ID
#
def drop_message(message_id):
    # ToDo: Refactor message storing to an array with indexed maps (possibly with DB in v2)
    for i in range(len(MESSAGE_STORE)):
        if MESSAGE_STORE[i][MESSAGE_JSON_ID] == message_id:
            MESSAGE_STORE.pop(i)
            break


##########################################################################################
# Add element to given path without duplicates at the end
#
# '' + 'bbb' -> ':bbb'
# ':aaa' + 'bbb' -> ':aaa:bbb'
# ':aaa:bbb' + 'bbb' -> ':aaa:bbb'
#
def extend_path(path, element):
    path_array = path.split(":")
    if path_array[len(path_array) - 1] != element:
        path = path + ":" + element
    return path


##########################################################################################
# Add actual cluster to distribution path
#
def add_cluster_to_message_path(message_id):
    # ToDo: Refactor message storing to an array with indexed maps (possibly with DB in v2)
    for message in MESSAGE_STORE:
        if message[MESSAGE_JSON_ID] == message_id:
            # Do some logging of the actual message path
            if MESSAGE_JSON_PATH not in message.keys():
                # Set this server cluster as root to the message path tag
                message[MESSAGE_JSON_PATH] = MESSAGE_PATH_SEP + NEXUS_SERVER_ROLE[ROLE_JSON_CLUSTER]
                # Log set root path event
                RNS.log(
                    "New message " + str(message[MESSAGE_JSON_ID]) + " has root path " + message[MESSAGE_JSON_PATH]
                )
            else:
                # Add this server cluster to message path
                message[MESSAGE_JSON_PATH] = \
                    extend_path(message[MESSAGE_JSON_PATH], NEXUS_SERVER_ROLE[ROLE_JSON_CLUSTER])

                # Log path extension event
                RNS.log(
                    "Path of message " + str(message[MESSAGE_JSON_ID]) + " was extended to " + message[
                        MESSAGE_JSON_PATH]
                )


##########################################################################################
# Validate/Drop/Migrate Message
#
def is_valid_message(message):
    # Invalid message if message version tag is missing
    if MESSAGE_JSON_VERSION not in message.keys():
        return False
    # Invalid message if message version tag is below 1
    elif message[MESSAGE_JSON_VERSION] != __message_version__:
        return False

    return True


##########################################################################################
# Validate message store
#
def validate_message_store():
    for message in MESSAGE_STORE.copy():
        if not is_valid_message(message):
            RNS.log(
                "Message " + str(message[MESSAGE_JSON_ID]) + " will be dropped due to deprecated message version"
            )
            # Drop invalid message from message store
            drop_message(message[MESSAGE_JSON_ID])
    # Update saved message store
    save_messages()


##########################################################################################
# Log message data
#
def log_message(message):
    # Log message data
    RNS.log("- Message '" + message[MESSAGE_JSON_MSG] + "'")
    RNS.log("- Version " + str(message[MESSAGE_JSON_VERSION]))
    RNS.log("- ID      " + str(message[MESSAGE_JSON_ID]))
    RNS.log("- Time    '" + message[MESSAGE_JSON_TIME] + "'")
    RNS.log("- Origin  " + message[MESSAGE_JSON_ORIGIN])
    RNS.log("- Via     " + message[MESSAGE_JSON_ORIGIN])
    if MESSAGE_JSON_PATH in message.keys():
        RNS.log("- Path   " + message[MESSAGE_JSON_PATH])


##########################################################################################
# LXM router socket for LXMF message handling
#
class NexusLXMSocket:
    def __init__(self, socket_identity=None, storage_path=None):
        # If identity was not given create a new for this lxm socket
        self.socket_identity = socket_identity
        if self.socket_identity is None:
            self.socket_identity = RNS.Identity()
        # If storage path was not set use default storage path
        self.storage_path = storage_path
        if self.storage_path is None:
            self.storage_path = LXMF_STORAGE_PATH
        # Check and create storage path if necessary
        if not os.path.isdir(self.storage_path):
            # Create storage path
            os.makedirs(self.storage_path)
            # Log that storage directory was created
            RNS.log("Created storage path " + self.storage_path)
        # Initialize lxm router
        self.lxm_router = LXMF.LXMRouter(storagepath=storage_path)
        # Initialize destination to be used as from destination when sending nexus messages to other nexus servers
        self.from_destination = RNS.Destination(
            self.socket_identity,
            RNS.Destination.OUT,
            RNS.Destination.SINGLE,
            APP_NAME, "messaging"
        )
        # Add XM destination to server role
        # With that it is distributed with the nexus server announce and can be stored with the subscription targets
        NEXUS_SERVER_ROLE[ROLE_JSON_LXM_DESTINATION] = self.from_destination.hash
        # Register callback to process received lxm deliverables
        self.lxm_router.register_delivery_callback(NexusLXMSocket.lxmf_delivery_callback)
        # Log updated server role
        RNS.log(
            "LXM messaging destination added to server role " + str(NEXUS_SERVER_ROLE)
        )

    def destination_hash(self):
        return self.from_destination.hash

    def announce(self):
        self.from_destination.announce()

    # noinspection DuplicatedCode
    @staticmethod
    def lxmf_delivery_callback(message):
        time_string = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(message.timestamp))
        signature_string = "Signature is invalid, reason undetermined"
        if message.signature_validated:
            signature_string = "Validated"
        else:
            if message.unverified_reason == LXMF.LXMessage.SIGNATURE_INVALID:
                signature_string = "Invalid signature"
            if message.unverified_reason == LXMF.LXMessage.SOURCE_UNKNOWN:
                signature_string = "Cannot verify, source is unknown"
        # Log LXM message received event
        RNS.log(
            "Received LXMF message " + time_string + " " + signature_string
        )

    def send_lxm_hello(self, destination_hash):
        # Create destination from hash with announced identity
        to_destination = RNS.Destination(
            self.socket_identity,
            RNS.Destination.OUT,
            RNS.Destination.SINGLE,
            APP_NAME, "messaging"
        )
        # Assemble Hello World message
        message_text = 'Hello Server ' + \
                       '012345678901234567890123456789012345678901234567890' + \
                       '012345678901234567890123456789012345678901234567890' + \
                       '012345678901234567890123456789012345678901234567890' + \
                       '012345678901234567890123456789012345678901234567890' + \
                       '012345678901234567890123456789012345678901234567890' + \
                       '012345678901234567890123456789012345678901234567890' + \
                       '012345678901234567890123456789012345678901234567890' + \
                       '012345678901234567890123456789012345678901234567890' + \
                       '012345678901234567890123456789012345678901234567890' + \
                       '012345678901234567890123456789012345678901234567890' + \
                       '012345678901234567890123456789012345678901234567890' + \
                       '012345678901234567890123456789012345678901234567890' + \
                       '012345678901234567890123456789012345678901234567890' + \
                       '012345678901234567890123456789012345678901234567890' + \
                       '012345678901234567890123456789012345678901234567890' + \
                       '012345678901234567890123456789012345678901234567890' + \
                       '012345678901234567890123456789012345678901234567890' + \
                       '012345678901234567890123456789012345678901234567890'
        message_title = 'Hello Nexus Server'
        # Create lxmessage and handle outbound to the target Nexus server with the lxm router
        lxm_message = LXMF.LXMessage(
            to_destination, self.from_destination,
            content=message_text, title=message_title,
            desired_method=LXMF.LXMessage.DIRECT
        )
        # lxm_message.register_delivery_callback(NexusLXMSocket.lxmf_delivery_callback)

        self.lxm_router.handle_outbound(lxm_message)

        RNS.log(
            "Hello Message sent to " + RNS.prettyhexrep(destination_hash) +
            " from " + RNS.prettyhexrep(self.from_destination.hash)
        )


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
    global NEXUS_LXM_SOCKET

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
    RNS.log("Nexus Server v" + __version__ + " using Message v" + __message_version__ + " startup configuration:")
    RNS.log("  --timeout=" + str(NEXUS_SERVER_TIMEOUT))
    RNS.log("  --longpoll=" + str(NEXUS_SERVER_LONGPOLL))
    RNS.log("  --port=" + str(NEXUS_SERVER_ADDRESS[1]))
    RNS.log("  --aspect=" + NEXUS_SERVER_ASPECT)
    RNS.log("  --role=" + str(NEXUS_SERVER_ROLE))
    RNS.log("  --bridge=" + str(BRIDGE_TARGETS))

    # Load messages from storage
    # Check if storage path is available
    if not os.path.isdir(MESSAGE_STORAGE_PATH):
        # Create storage path
        os.makedirs(MESSAGE_STORAGE_PATH)
        # Log that storage directory was created
        RNS.log(
            "Created storage path " + MESSAGE_STORAGE_PATH
        )
    # Check if we can read some messages from storage
    if os.path.isfile(MESSAGE_STORAGE_FILE):
        try:
            file = open(MESSAGE_STORAGE_FILE, "rb")
            MESSAGE_STORE = msgpack.unpackb(file.read())
            file.close()
            RNS.log(
                str(len(MESSAGE_STORE)) + " messages loaded from storage: " + MESSAGE_STORAGE_FILE
            )
        except Exception as e:
            RNS.log("Could not load messages from " + MESSAGE_STORAGE_FILE)
            RNS.log("The contained exception was: %s" % (str(e)))
        # Drop all messages with deprecated or missing message version
        validate_message_store()
        # Log how many have survived validation
        RNS.log(
            str(len(MESSAGE_STORE)) + " messages left after validation"
        )
    else:
        RNS.log("No messages to load from " + MESSAGE_STORAGE_FILE)

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

    # Create LXMF router socket with this server as source endpoint
    NEXUS_LXM_SOCKET = NexusLXMSocket()

    # Check if we have bridge links configured
    if len(BRIDGE_TARGETS) > 0:
        # Initial synchronisation Part 1
        # Retrieve and process message buffers from bridged targets
        # Log sync start
        RNS.log(
            "Initial synchronization - GET and digest messages from bridged servers"
        )
        # Loop through all bridge targets
        for bridge_target in BRIDGE_TARGETS:
            try:
                # Use GET Request to pull message buffer from bridge server
                response = requests.get(
                    url=bridge_target[BRIDGE_JSON_URL],
                    headers={'Content-type': 'application/json'}
                )
                # Log GET Request
                RNS.log(
                    "Pulled from bridge to '" + bridge_target[BRIDGE_JSON_CLUSTER] +
                    "' with GET request " + bridge_target[BRIDGE_JSON_URL]
                )
                # Check if GET was successful
                # If so, parse response body into message buffer and digest it
                if response.ok:
                    # Parse json bytes into message array of json maps
                    remote_buffer = json.loads(response.content)
                    # Log GET result
                    RNS.log(
                        "GET request was successful with " + str(len(remote_buffer)) + " Messages received"
                    )

                    # Digest received messages
                    digest_messages(remote_buffer, bridge_target[BRIDGE_JSON_CLUSTER])
                else:
                    # Log GET failure
                    RNS.log(
                        "GET request has failed with reason: " + response.reason
                    )
            except Exception as e:
                RNS.log("Could not complete GET request " + bridge_target[BRIDGE_JSON_URL])
                RNS.log("The contained exception was: %s" % (str(e)))

        # Log start of message distribution after digesting bridge link buffers
        RNS.log(
            "Initial synchronization - Distribute messages marked as selected for distribution"
        )
        # Distribute all messages marked with merge tag
        # Loop through massage buffer and distribute all messages that have been tagged
        for message in copy.deepcopy(MESSAGE_STORE):
            # Check if message has a merge tag stating the origin bridge tag
            if MERGE_JSON_TAG in message.keys():
                # Remove tag at the original buffer (if still there)
                # Can be invalid in case any incoming message may have caused drop of that message
                untag_message(message[MESSAGE_JSON_ID], MERGE_JSON_TAG)
                # Distribute message to distribution targets and other bridge targets
                # Copy of message still has bridge tan to indicate its origin
                distribute_message(message)

        # Save message buffer after synchronisation
        save_messages()
        # Log completion of initial synchronization
        RNS.log(
            "Initial synchronization - Distribution completed"
        )
    else:
        RNS.log(
            "No bridge targets configured to use for initial synchronization"
        )

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

    # Flush pending log
    sys.stdout.flush()


##########################################################################################
# Announce the server to the reticulum network
#
# Calling this function will start a timer that will call this function again after the
# specified re-announce period.
#
def single_announce_server():
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
        "Server announcement sent with app_data: " + str(NEXUS_SERVER_ROLE)
    )


def announce_server():
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
    # Create multithreading http server with given address and port to listen for json app interaction
    httpd = ThreadingHTTPServer(NEXUS_SERVER_ADDRESS, ServerRequestHandler)
    # Log launch with aspect and address/port used
    RNS.log(
        "Serving '" + APP_NAME + '.' + NEXUS_SERVER_ASPECT + "' at %s:%d" % NEXUS_SERVER_ADDRESS
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
    global NEXUS_LXM_SOCKET

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

        # Check if we have app data received
        if app_data is None:
            # Log app data missing
            RNS.log("The announce is ignored because it contained no valid nexus role dictionary")
            return

        # Recreate nexus role dict from received app data
        announced_role = pickle.loads(app_data)
        # Log role
        RNS.log(
            "The announce contained the following nexus role: " +
            str(announced_role)
        )

        # Get dict key and timestamp for distribution identity registration
        dict_key = RNS.prettyhexrep(destination_hash)
        dict_time = int(time.time())
        # Get lxm messaging destination out of role dict
        lxm_messaging_destination = announced_role[ROLE_JSON_LXM_DESTINATION]

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

                # Say Hello via LXM router
                NEXUS_LXM_SOCKET.send_lxm_hello(lxm_messaging_destination)
                RNS.log(
                    "Send Hello to lxm messaging destination " + RNS.prettyhexrep(lxm_messaging_destination)
                )

            else:
                # Log that we just updated new subscription
                RNS.log(
                    "Subscription for " + RNS.prettyhexrep(destination_hash) +
                    " will be updated"
                )
            # Register for update destination as valid distribution target
            DISTRIBUTION_TARGETS[dict_key] = (
                dict_time,
                announced_identity,
                destination_hash,
                lxm_messaging_destination
            )

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
                        "Distribution destination " + RNS.prettyhexrep(DISTRIBUTION_TARGETS[element][2]) +
                        " removed because of timeout"
                    )
                    # Actually remove destination from dict
                    DISTRIBUTION_TARGETS.pop(element)

                # If actual is still valid log it
                RNS.log(
                    "Registered Server " + destination + " last heard " + str(last_heard) + "sec ago"
                )
        else:
            # Announce should be ignored since it belongs to a different cluster, and we are not eligible to
            # link with that cluster as gateway too
            RNS.log(
                "Announced nexus target was ignored"
            )

    # Flush pending log
    sys.stdout.flush()


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
# The received message is processed and the forwarded to distribution
#
def packet_callback(data, _packet):
    # Reconstruct original python object
    # In this case it was a python dictionary containing the json message
    message = pickle.loads(data)

    # Check if message is valid
    if is_valid_message(message):
        # Log message received by distribution event
        RNS.log(
            "Valid message received via RNS packet"
        )
        # Log message data
        log_message(message)

        # Process, store and distribute message as required
        if process_incoming_message(message):
            # Distribute message to all registered or bridged nexus servers
            distribute_message(message)

        # Save message buffer after synchronisation
        save_messages()
    else:
        # Message failed validation and is ignored
        RNS.log(
            "Received RNS packet failed version validation and is ignored"
        )

    # Flush pending log
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
        body = self.rfile.read(length)
        # Log message received event
        # RNS.log("HTTP POST Body:" + str(body))
        # Parse JSON
        message = json.loads(body)

        # Do some logging of the outcome of the POST processing so far
        if MESSAGE_JSON_PATH not in message.keys():
            # Log new client message received event
            RNS.log(
                "HTTP POST received from client"
            )
            # ToDo Set message version correctly at client side (actually not implemented in client)
            message[MESSAGE_JSON_VERSION] = __message_version__
            RNS.log("Message version set to " + __message_version__)
        else:
            # Log new client message received event
            RNS.log(
                "HTTP POST received from bridge"
            )

        # Check if message is valid
        if is_valid_message(message):
            # Check if incoming message was a client sent message and does not have a path tag
            # Bridged messages have a path tag set, local posts of new messages does not.

            # If message has no 'origin' set use this server as origin
            if MESSAGE_JSON_ORIGIN not in message.keys():
                # Set Origin to this server
                message[MESSAGE_JSON_ORIGIN] = RNS.prettyhexrep(NEXUS_SERVER_DESTINATION.hash)

            # If message has no 'via' set use this server as via
            if MESSAGE_JSON_VIA not in message.keys():
                # Set Via to this server
                message[MESSAGE_JSON_VIA] = RNS.prettyhexrep(NEXUS_SERVER_DESTINATION.hash)

            # If message has no ID yet create one
            if MESSAGE_JSON_ID not in message.keys():
                # Create a timestamp and add that as ID to the message map
                message[MESSAGE_JSON_ID] = int(time.time() * 100000)

            # Log updated message data
            log_message(message)

            # Build and return JSON success response
            self._set_headers()
            self.wfile.write(json.dumps({'success': True}).encode('utf-8'))

            # Process, store and distribute message as required
            if process_incoming_message(message):
                # Distribute message to all registered or bridged nexus servers
                distribute_message(message)

            # Save message buffer after synchronisation
            save_messages()

        else:
            # Message failed validation and is ignored
            RNS.log(
                "Received POST request failed version validation and is ignored"
            )

        # Flush pending log
        sys.stdout.flush()

    # Set request options
    def do_OPTIONS(self):
        # Send allow-origin header and clearance for GET and POST requests
        self.send_response(HTTPStatus.NO_CONTENT)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST')
        self.send_header('Access-Control-Allow-Headers', 'content-type')
        self.end_headers()


##########################################################################################
# Digest an array of messages into the global message store
#
# This is used for merging available message buffers into one buffer (Synchronization during server startup)
#
def digest_messages(merge_buffer, cluster):
    # Process all messages inside pulled buffer as if they have been standard incoming messages
    # Distribution however will be performed only for messages that got a cluster tag and are still in the buffer
    # after all messages have been digested
    for message in merge_buffer:
        # Get message id for logging
        if MESSAGE_JSON_ID in message.keys():
            message_id = message[MESSAGE_JSON_ID]
        else:
            message_id = MESSAGE_ID_NOT_SET
        # Check if message to digest is valid
        if is_valid_message(message):
            # Digest the message into the message buffer and return ID if we need to distribute the message
            message_id = process_incoming_message(message)
            # If distribution is due, tag message as new (distribution will occur as soon as we have completed
            # processing of all messages in the pulled remote buffer)
            if message_id:
                # Tag message with given cluster tag
                tag_message(message_id, BRIDGE_JSON_CLUSTER, cluster)
        else:
            RNS.log(
                "Message " + str(message_id) + " pulled from bridge to cluster '" + cluster +
                "' has invalid version and is dropped"
            )


##########################################################################################
# Process incoming message
#
# This function is called by the reticulum paket handler (message was received as reticulum message) and by the POST
# request handler in case it was received from a client or bridge POST request
# Its Job is to check if we need to add/insert the message in the message buffer or should it be ignored
def process_incoming_message(message):
    # If message is more recent than the oldest message in the buffer
    # and has not arrived earlier, then add/insert message at the correct position and
    # Get actual timestamp from message
    message_id = message[MESSAGE_JSON_ID]
    # Get actual number of messages in the buffer
    message_store_size = len(MESSAGE_STORE)

    if message_store_size == 0:
        # First message arrived event
        RNS.log(
            "Message " + str(message_id) +
            " is first message in the buffer"
        )
        # Append the JSON message map to the message store at last position
        MESSAGE_STORE.append(message)
    else:
        # At least one message is already there and need to be checked for insertion
        # loop through all messages and check if we have to store and distribute it
        for i in range(0, message_store_size):
            # Check if we already have that message at the actual buffer position
            if message_id == MESSAGE_STORE[i][MESSAGE_JSON_ID]:
                # Timestamp did match now check if message does too
                if message[MESSAGE_JSON_MSG] == MESSAGE_STORE[i][MESSAGE_JSON_MSG]:
                    # Log that we have that one already
                    RNS.log(
                        "Message " + str(message_id) +
                        " storing and distribution not necessary because message is already in the buffer"
                    )
                    # Since we consider a message at the buffer has been distributed already we can exit this function
                    # Flush pending log
                    sys.stdout.flush()
                    # Return False to indicate that distribution is not required
                    return False

                # Message has same time stamp but differs
                else:
                    # Log message insertion with same timestamp
                    RNS.log(
                        "Message " + str(message_id) +
                        " has a duplicate timestamp but differs (Message will be inserted in timeline)"
                    )
                    # Insert it at the actual position
                    MESSAGE_STORE.insert(i, message)
                    # Message processing completed
                    # Exit loop
                    break
            # Timestamps to not mach
            # lets check if it is to be inserted here
            elif message_id < MESSAGE_STORE[i][MESSAGE_JSON_ID]:
                # Yes it is
                # Log message insertion with same timestamp
                RNS.log(
                    "Message " + str(message_id) +
                    " will be inserted in timeline"
                )
                # Insert it at the actual position
                MESSAGE_STORE.insert(i, message)
                # Message processing completed
                # Exit loop
                break
            # Continue until we find the place to insert it, or
            # we have checked the latest entry in the buffer (i=size-1)
            # If we are there than we can append and distribute it
            # After that has happened we terminate the loop as well
            # The loop will never be terminated automatically
            if i == message_store_size - 1:
                # Log message append
                RNS.log(
                    "Message " + str(message_id) +
                    " is most recent and will be appended to timeline"
                )
                # Append the JSON message map to the message store at last position
                MESSAGE_STORE.append(message)
                # Message processing completed
                # Exit loop
                break

    # If we pass this point of digestion we have new message received
    # Update the distribution path of the message
    add_cluster_to_message_path(message_id)

    # No we are done with adding/inserting
    # Lets check buffer size if defined limit is exceeded now
    # and if so pop oldest message until we are back in the limit
    while True:
        length = len(MESSAGE_STORE)
        if length > MESSAGE_BUFFER_SIZE:
            # Log message pop
            RNS.log(
                "Maximum message count of " + str(MESSAGE_BUFFER_SIZE) +
                " exceeded. Oldest message is dropped now"
            )
            # If limit is exceeded just drop first (oldest) element of list
            MESSAGE_STORE.pop(0)
        else:
            break

    # Return message_id of the processed message that is cleared for distribution
    return message_id


##########################################################################################
# Message distribution to registered nexus serves
#
# The given message (json map) will be distributed to all linked nexus servers that have
# updated their availability by a re-announcement prior the expiration period.
# While we iterate through the list all already expired targets are dropped from the list.
# Same expiration management is done during announcement processing.
# Additionally, the message is bridged to all registered bridge targets.
#
def distribute_message(message):
    # Process bridge targets

    # Loop through all registered bridge targets
    for bridge_target in BRIDGE_TARGETS:
        # Check if actual message was pulled from that target; aka has the same cluster tag like the bridge target
        # Check if we have a cluster tag
        if BRIDGE_JSON_CLUSTER in message.keys():
            # Check if it is the same as the bridge target
            if message[BRIDGE_JSON_CLUSTER] == bridge_target[BRIDGE_JSON_CLUSTER]:
                # Log that this message was actually received from that bridge
                RNS.log(
                    "Message distribution to bridge '" + bridge_target[BRIDGE_JSON_CLUSTER] +
                    "' was suppressed because message was received from that bridge"
                )
                # Continue with next bridge target
                continue

        # Now lets check if we can find the target cluster in the path of the message
        # If it is there the message has traveled through that cluster already and does not need to go there again
        if message[MESSAGE_JSON_PATH].find(bridge_target[BRIDGE_JSON_CLUSTER]) != -1:
            # Log that this message was actually received from that bridge
            RNS.log(
                "Message distribution to bridge '" + bridge_target[BRIDGE_JSON_CLUSTER] +
                "' was suppressed because its path '" + message[MESSAGE_JSON_PATH] +
                "' contains that cluster already"
            )
            # Continue with next bridge target
            continue

        # Remove cluster tag from message
        if BRIDGE_JSON_CLUSTER in message.keys():
            message.pop(BRIDGE_JSON_CLUSTER)

        # Use POST to send message to bridge nexus server link
        try:
            response = requests.post(
                url=bridge_target[BRIDGE_JSON_URL],
                json=message,
                headers={'Content-type': 'application/json'}
            )
            # Check if request was successful
            if response.ok:
                # Log that we bridged a message
                RNS.log(
                    "POST request " + bridge_target[BRIDGE_JSON_URL] +
                    " to bridge '" + bridge_target[BRIDGE_JSON_CLUSTER] + "' completed successfully"
                )
            else:
                # Log POST failure
                RNS.log(
                    "POST request " + bridge_target[BRIDGE_JSON_URL] +
                    " to bridge '" + bridge_target[BRIDGE_JSON_CLUSTER] +
                    "' failed with reason: " + response.reason
                )
        except Exception as e:
            RNS.log("Could not complete POST request " + bridge_target[BRIDGE_JSON_URL])
            RNS.log("The contained exception was: %s" % (str(e)))

    # Process distribution targets

    # Loop through all registered distribution targets
    # Remove all targets that have not announced them self within given timeout period
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
            # Continue with next distribution target
            continue
        # Back propagation to forwarder suppression
        # If forwarder of message to distribute equals target suppress distributing it
        elif message[MESSAGE_JSON_VIA] == RNS.prettyhexrep(remote_server.hash):
            # Log message received by distribution event
            RNS.log(
                "Distribution to " + RNS.prettyhexrep(remote_server.hash) +
                " was suppressed because message was forwarded from that server"
            )
            # Continue with next distribution target
            continue
        else:
            # Set new forwarder (VIA) id to message
            # Overwrite previous forwarder id
            message[MESSAGE_JSON_VIA] = RNS.prettyhexrep(NEXUS_SERVER_DESTINATION.hash)

            # Get time stamp from target dict
            timestamp = DISTRIBUTION_TARGETS[target][0]
            # Get actual time from system
            actual_time = int(time.time())

            # Check if target has not expired yet
            if (actual_time - timestamp) < NEXUS_SERVER_TIMEOUT:
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


#######################################################
# Program Startup
#
# Default python entrypoint with processing the give commandline parameters
#
def signal_handler(_signal, _frame):
    print("exiting")

    # Flush pending log
    sys.stdout.flush()
    # Exit
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

        # Flush pending log
        sys.stdout.flush()

    # Handle keyboard interrupt aka ctrl-C to exit server
    except KeyboardInterrupt:
        print("Server terminated by ctrl-c")

        # Flush pending log
        sys.stdout.flush()
        sys.exit(0)
