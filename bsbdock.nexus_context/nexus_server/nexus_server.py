#!/usr/bin/env python3
###########################################################################################
#  ____   _____ ____   _   _                      _____
# |  _ \ / ____|  _ \ | \ | |                    / ____|                         
# | |_) | (___ | |_) ||  \| | _____  ___   _ ___| (___   ___ _ ____   _____ _ __ 
# |  _ < \___ \|  _ < | . ` |/ _ \ \/ / | | / __|\___ \ / _ \ '__\ \ / / _ \ '__|
# | |_) |____) | |_) || |\  |  __/>  <| |_| \__ \____) |  __/ |   \ V /  __/ |   
# |____/|_____/|____(_)_| \_|\___/_/\_\\__,_|___/_____/ \___|_|    \_/ \___|_|   
#
# Copyright (c) 2020 Stephan Becker / Becker-Systemberatung, MIT License
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this
# software and associated documentation files (the "Software"), to deal in the Software
# without restriction, including without limitation the rights to use, copy, modify, merge,
# publish, distribute, sublicense, and/or sell copies of the Software, and to permit
# persons to whom the Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies
# or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR
# PURPOSE AND NON INFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE
# FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
# OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.
#
# This software contains and uses Reticulum, NomadNet and LXMF
# Copyright (c) 2016-2022 Mark Qvist / unsigned.io, MIT License
#
import sys
import os
import time
import argparse
import copy

import json
import pickle
import string

import signal
import threading
import requests
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from http import HTTPStatus

import LXMF
import RNS
import RNS.vendor.umsgpack as umsgpack

##########################################################################################
# Global variables
#

# Versions used
__server_version__ = "1.4.0.1"
__role_version__ = "2"
__command_version__ = "1"
__message_version__ = "4.2"

# A moment to process background stuff
DIGESTION_DELAY = 0.1

# Message storage
MESSAGE_STORAGE_PATH = os.path.expanduser("~") + "/.nexus/storage"
MESSAGE_STORAGE_FILE = MESSAGE_STORAGE_PATH + "/messages.umsgpack"

# LXMF storage
LXMF_STORAGE_PATH = os.path.expanduser("~") + "/.nexus/lxmf"

# Message buffer used for actually server messages
MESSAGE_STORE = []  # type: list[dict]
# Number of messages hold (Size of message buffer)
MESSAGE_BUFFER_SIZE = 20
# Number of messages pulled from remote server as update
MAXIMUM_UPDATE_MESSAGES = 20

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

# Tags and constants used in nexus server
SERVER_JSON_VERSION = "serv"
# Tags and constants used in nexus command
COMMAND_JSON_VERSION = "cmdv"
COMMAND_JSON_CMD = "p0"
COMMAND_JSON_P1 = "p1"
COMMAND_JSON_P2 = "p2"
COMMAND_JSON_P3 = "p3"
# Tags and constants used in messages
MESSAGE_JSON_VERSION = "msgv"
MESSAGE_JSON_TIME = "time"
MESSAGE_JSON_MSG = "msg"
MESSAGE_JSON_ID = "id"
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
BRIDGE_JSON_ONLINE = "online"
BRIDGE_JSON_POLL = "poll"
# Tags used during message buffer merge (tag to indicate is selected for distribution)
MERGE_JSON_TAG = "tag"

# Server to server protokoll used for automatic subscription (Cluster and Gateway)
# The LXM Destination is added with the LXM socket instantiation
# Role Example: {'c':'ClusterName','g':'GatewayName', 'l': latest_id}
ROLE_JSON_CLUSTER = "cluster"
ROLE_JSON_GATEWAY = "gate"
ROLE_JSON_LAST = "last"
ROLE_JSON_VERSION = "rolv"

# Full version dict added to role
__full_version__ = {
    SERVER_JSON_VERSION: __server_version__,
    ROLE_JSON_VERSION: __role_version__,
    COMMAND_JSON_VERSION: __command_version__,
    MESSAGE_JSON_VERSION: __message_version__
}
VERSION_JSON_VERSION = "ver"

# Some Server default values used to announce nexus servers to reticulum
# APP_NAME = "nexus"
APP_NAME = "nexus"
NEXUS_SERVER_ASPECT = "home"

# Default server cluster that is announced to be subscribed to
# This one can be used to run not connected server names by just giving all servers different cluster names
# These servers can later be interconnected by using gateway names (see server role)
DEFAULT_CLUSTER = "home"
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
NEXUS_SERVER_LONGPOLL: int = int(NEXUS_SERVER_TIMEOUT / 2.5)
# Delay of initial announcement of this server to the network
INITIAL_ANNOUNCEMENT_DELAY = 5

# Nexus LXM Socket
# noinspection PyTypeChecker
NEXUS_LXM_SOCKET = None  # type: NexusLXMSocket

# Command IDs
# Check if command is add message to buffer command
CMD_ADD_MESSAGE = 0
CMD_REQUEST_MESSAGES_SINCE = 1

##########################################################################################
# Helper functions
#


##########################################################################################
# Remove all whitespaces
#
def remove_whitespace(in_string: str):
    return in_string.translate(str.maketrans(dict.fromkeys(string.whitespace)))


##########################################################################################
# Init Bridge Online Status
#
def init_bridges():
    for bridge in BRIDGE_TARGETS:
        bridge[BRIDGE_JSON_ONLINE] = False


##########################################################################################
# Save messages to storage file
#
def save_messages():
    # Check if storage file is there
    try:
        save_file = open(MESSAGE_STORAGE_FILE, "wb")
        save_file.write(umsgpack.packb(MESSAGE_STORE))
        save_file.close()
        RNS.log("Messages saved to storage file " + MESSAGE_STORAGE_FILE, RNS.LOG_DEBUG)

    except Exception as err:
        RNS.log("Could not save message to storage file " + MESSAGE_STORAGE_FILE, RNS.LOG_ERROR)
        RNS.log("The contained exception was: %s" % (str(err)), RNS.LOG_ERROR)


##########################################################################################
# Load messages from storage file
#
def load_messages():
    global MESSAGE_STORE

    # Load messages from storage
    # Check if storage path is available
    if not os.path.isdir(MESSAGE_STORAGE_PATH):
        # Create storage path
        os.makedirs(MESSAGE_STORAGE_PATH)
        # Log that storage directory was created
        RNS.log("Created storage path " + MESSAGE_STORAGE_PATH, RNS.LOG_NOTICE)
    # Check if we can read some messages from storage
    if os.path.isfile(MESSAGE_STORAGE_FILE):
        try:
            file = open(MESSAGE_STORAGE_FILE, "rb")
            MESSAGE_STORE = umsgpack.unpackb(file.read())
            file.close()
            RNS.log(str(len(MESSAGE_STORE)) + " messages loaded from storage: " + MESSAGE_STORAGE_FILE, RNS.LOG_DEBUG)
        except Exception as e:
            RNS.log("Could not load messages from " + MESSAGE_STORAGE_FILE, RNS.LOG_ERROR)
            RNS.log("The contained exception was: %s" % (str(e)), RNS.LOG_ERROR)
        # Drop all messages with deprecated or missing message version
        validate_message_store()
        # Log how many have survived validation
        RNS.log(str(len(MESSAGE_STORE)) + " messages left after validation", RNS.LOG_DEBUG)
    else:
        RNS.log("No messages to load from " + MESSAGE_STORAGE_FILE, RNS.LOG_EXTREME)


##########################################################################################
# Load message buffers from all configured bridges, merge them into the messages buffer of
# this server.
# Messages exceeding the maximum message count limit will be dropped.
# Messages that have newly arrived in the buffer are distributed to all relevant nexus servers
# over the configured bridges or registered as active distribution targets by earlier announces.
#
def sync_from_bridges():
    # Check if we have bridge links configured
    if len(BRIDGE_TARGETS) > 0:
        # Initial synchronisation Part 1
        # Retrieve and process message buffers from bridged targets
        # Log sync start
        RNS.log("Get messages from bridged servers", RNS.LOG_INFO)
        # Loop through all bridge targets
        for bridge_target in BRIDGE_TARGETS:
            # Check if we have the online status key inside the target
            if BRIDGE_JSON_ONLINE not in bridge_target.keys():
                # Initialize it with False
                bridge_target[BRIDGE_JSON_ONLINE] = False
            # Check if we have the poll key inside the target
            if BRIDGE_JSON_POLL not in bridge_target.keys():
                # Initialize it with False
                bridge_target[BRIDGE_JSON_POLL] = False
            # Only during initial sync all the bridges need to be pulled
            # Later during long poll events it might be OK to pull again only if the status has been reset
            # to False (e.g. after a bridge post failed)
            # Targets with poll=True will be pulled avery time regardless of its online status
            if not bridge_target[BRIDGE_JSON_ONLINE] or bridge_target[BRIDGE_JSON_POLL]:
                # Pull message buffer from bridge target
                try:
                    # Use GET Request to pull message buffer from bridge server
                    response = requests.get(
                        url=bridge_target[BRIDGE_JSON_URL],
                        headers={'Content-type': 'application/json'}
                    )
                    # Log GET Request
                    RNS.log(
                        "Pulled from bridge to '" + bridge_target[BRIDGE_JSON_CLUSTER] +
                        "' with GET request " + bridge_target[BRIDGE_JSON_URL],
                        RNS.LOG_VERBOSE
                    )
                    # Check if GET was successful
                    # If so, parse response body into message buffer and digest it
                    if response.ok:
                        # Set bridge status to online
                        bridge_target[BRIDGE_JSON_ONLINE] = True
                        # Parse json bytes into message array of json maps
                        remote_buffer = json.loads(response.content)
                        # Log GET result
                        RNS.log(
                            "GET request was successful with " + str(len(remote_buffer)) + " Messages received",
                            RNS.LOG_VERBOSE
                        )

                        # Digest received messages
                        digest_messages(remote_buffer, bridge_target[BRIDGE_JSON_CLUSTER])
                    else:
                        # Set bridge status to offline
                        bridge_target[BRIDGE_JSON_ONLINE] = False
                        # Log GET failure
                        RNS.log("GET request has failed with reason: " + response.reason, RNS.LOG_ERROR)

                except Exception as e:
                    RNS.log("Could not complete GET request " + bridge_target[BRIDGE_JSON_URL], RNS.LOG_ERROR)
                    RNS.log("The contained exception was: %s" % (str(e)), RNS.LOG_ERROR)

        # Log start of message distribution after digesting bridge link buffers
        RNS.log("Distribute messages marked as selected for distribution after bridge pull digestion", RNS.LOG_DEBUG)

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
        RNS.log("Bridge pull and distribution completed", RNS.LOG_DEBUG)
    else:
        RNS.log("No bridge targets configured", RNS.LOG_VERBOSE)


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
                    "New message " + str(message[MESSAGE_JSON_ID]) + " has root path " + message[MESSAGE_JSON_PATH],
                    RNS.LOG_DEBUG
                )
            else:
                # Add this server cluster to message path
                message[MESSAGE_JSON_PATH] = \
                    extend_path(message[MESSAGE_JSON_PATH], NEXUS_SERVER_ROLE[ROLE_JSON_CLUSTER])

                # Log path extension event
                RNS.log(
                    "Path of message " + str(message[MESSAGE_JSON_ID]) +
                    " was extended to " + message[MESSAGE_JSON_PATH],
                    RNS.LOG_DEBUG
                )


##########################################################################################
# Validate/Drop/Migrate Command
#
def validate_command(command):
    # Command signature to invalidate a message
    invalid_command = {}

    # Invalid command if command version tag is missing
    if COMMAND_JSON_VERSION not in command.keys():
        # Set actual command to invalid command
        command = invalid_command
    # Invalid command if command version does not match actual command version
    elif command[COMMAND_JSON_VERSION] > __command_version__:
        # Command has higher version that this can handle
        RNS.log(
            "Command is invalidated because command version " + str(command[COMMAND_JSON_VERSION]) +
            " is ahead of server command version " + __command_version__,
            RNS.LOG_WARNING
        )
        # Set actual command to invalid command
        command = invalid_command
    elif command[COMMAND_JSON_VERSION] < __command_version__:
        # Command version is lower and possibly needs migration
        RNS.log(
            "Command version " + str(command[COMMAND_JSON_VERSION]) +
            " is below server command version " + __command_version__,
            RNS.LOG_DEBUG
        )

        # Actual no migration applied, message will just be invalidated
        RNS.log("Command is invalidated because no migration possible", RNS.LOG_INFO)
        # Set actual command to invalid command
        command = invalid_command

    # Return invalidated or validated (migrated) message
    return command


def is_valid_command(command):
    # Invalid message if message version tag is missing
    if COMMAND_JSON_VERSION not in command.keys():
        return False
    # Invalid message if message version tag is not matching actual command version
    elif command[COMMAND_JSON_VERSION] != __command_version__:
        return False

    return True


##########################################################################################
# Validate/Drop/Migrate Message
#
def validate_message(message):
    # Message signature to invalidate a message
    invalid_message = {}

    # Check for mandatory message key
    # Without that continuing is pointless
    if not (MESSAGE_JSON_MSG in message.keys()):
        # Return invalid message
        message = invalid_message
        return message

    # Invalid message if message version tag is missing
    if MESSAGE_JSON_VERSION not in message.keys():
        # If we don't have a message version set actual version
        message[MESSAGE_JSON_VERSION] = __message_version__

    # If message has no 'origin' set use this server as origin
    if MESSAGE_JSON_ORIGIN not in message.keys():
        # Set Origin to this server
        message[MESSAGE_JSON_ORIGIN] = RNS.prettyhexrep(NEXUS_LXM_SOCKET.destination_hash())

    # If message has no 'via' set use this server as via
    if MESSAGE_JSON_VIA not in message.keys():
        # Set Via to this server
        message[MESSAGE_JSON_VIA] = RNS.prettyhexrep(NEXUS_LXM_SOCKET.destination_hash())

    # If message has no ID yet create one
    if MESSAGE_JSON_ID not in message.keys():
        # Create a timestamp and add that as ID to the message map
        message[MESSAGE_JSON_ID] = int(time.time() * 100000)

    # Invalid message if message version does not match actual message version
    elif message[MESSAGE_JSON_VERSION] > __message_version__:
        # Message has higher version that this can handle
        RNS.log(
            "Message is invalidated because message version " + str(message[MESSAGE_JSON_VERSION]) +
            " is ahead of server message version " + __message_version__,
            RNS.LOG_WARNING
        )
        # Set actual message to invalid message
        message = invalid_message
    elif message[MESSAGE_JSON_VERSION] < __message_version__:
        # Message version is lower and possibly needs migration
        RNS.log(
            "Message version " + str(message[MESSAGE_JSON_VERSION]) +
            " is below server message version " + __message_version__,
            RNS.LOG_DEBUG
        )

        # Check for message version 3
        if message[MESSAGE_JSON_VERSION] == "3":
            # Messages v3 can be forwarded to be actual ones
            # Used to handle old clients still posting v3
            message[MESSAGE_JSON_VERSION] = __message_version__
            # Log message migration
            RNS.log("Message was elevated from v3 to v" + __message_version__, RNS.LOG_WARNING)

        else:
            # Actual no migration applied, message will just be invalidated
            RNS.log("Message is invalidated because no migration possible", RNS.LOG_WARNING)
            # Set actual message to invalid message
            message = invalid_message

    # Return invalidated or validated (migrated) message
    return message


def is_valid_message(message):
    # Invalid message if message version tag is missing
    if MESSAGE_JSON_VERSION not in message.keys():
        return False
    # Invalid message if message version tag is not matching actual message version
    elif message[MESSAGE_JSON_VERSION] != __message_version__:
        return False

    return True


##########################################################################################
# Validate/Drop/Migrate Announcement
#
def validate_role(server_role):
    # Server role signature to invalidate an announce
    invalid_role = {}

    # Invalid role if version key is missing
    if VERSION_JSON_VERSION not in server_role.keys():
        RNS.log("Announced role " + str(server_role) + " has no version key", RNS.LOG_ERROR)
        return invalid_role

    # Get version dict from announced role
    version_dict = server_role[VERSION_JSON_VERSION]

    # Invalid role if role version is missing
    if ROLE_JSON_VERSION not in version_dict.keys():
        RNS.log("Announced versions " + str(server_role) + " doe not contain role version", RNS.LOG_ERROR)
        return invalid_role

    # Get role from version dict
    role_version = version_dict[ROLE_JSON_VERSION]

    # Warn if role version does not match actual server version
    if role_version != __role_version__:
        # Server version does not match
        RNS.log(
            "Announced role version " + role_version +
            " does not match server role version " + __role_version__,
            RNS.LOG_WARNING
        )

        # Replace this section with migration if one is possible
        # Actual no migration implemented, announced role is considered valid

    # Return invalidated or validated (migrated) message
    return server_role


def is_valid_role(server_role):
    # Invalid role if version key is missing
    if VERSION_JSON_VERSION not in server_role.keys():
        RNS.log("Role " + str(server_role) + " has no version key", RNS.LOG_ERROR)
        return False

    # Get version dict from announced role
    version_dict = server_role[VERSION_JSON_VERSION]

    # Invalid role if role key is missing
    if ROLE_JSON_VERSION not in version_dict.keys():
        RNS.log("Version dictionary " + str(server_role) + " does not contain role version", RNS.LOG_ERROR)
        return False

    # Get role from version dict
    role_version = version_dict[ROLE_JSON_VERSION]

    # Invalid role if server version does not match actual server version
    if role_version == __role_version__:
        return True
    # If role version is below actual version server shall be able to process announcement properly
    if role_version < __role_version__:
        # Log Info
        RNS.log("Role version " + role_version + " is deprecated.", RNS.LOG_NOTICE)
        return True
    # Announcements of future releases may cause issues
    else:
        # Log Warning
        RNS.log(
            "Role server version " + server_role[VERSION_JSON_VERSION][ROLE_JSON_VERSION] +
            " is newer than actual server version and considered invalid.", RNS.LOG_WARNING
        )
        return False


##########################################################################################
# Validate message store
#
def validate_message_store():
    # Get Store size
    store_size = len(MESSAGE_STORE)
    # If we have any message, validate messages
    if store_size > 0:
        # Loop through all messages from end to start, so we can pop items securely
        for i in range(store_size):
            # Validation/Migration of the actual messages in buffer
            MESSAGE_STORE[store_size - i - 1] = validate_message(MESSAGE_STORE[store_size - i - 1])
            if not is_valid_message(MESSAGE_STORE[store_size - i - 1]):
                MESSAGE_STORE.pop(store_size - i - 1)
        # Update saved message store
        save_messages()


##########################################################################################
# Validate message store
#
def latest_message_id():
    store_size = len(MESSAGE_STORE)
    if store_size < 1:
        # IF we have no messages yet id is 0 since unix epoch
        return 0
    else:
        # Return message id which indicates time since unix epoch
        return MESSAGE_STORE[store_size - 1][MESSAGE_JSON_ID]


##########################################################################################
# Log message data
#
def log_nexus_message(message):
    # Log message data
    RNS.log("Nexus Message Details:", RNS.LOG_VERBOSE)
    RNS.log("- Message '" + message[MESSAGE_JSON_MSG] + "'", RNS.LOG_VERBOSE)
    RNS.log("- Version " + str(message[MESSAGE_JSON_VERSION]), RNS.LOG_VERBOSE)
    RNS.log("- ID      " + str(message[MESSAGE_JSON_ID]), RNS.LOG_VERBOSE)
    RNS.log("- Time    '" + message[MESSAGE_JSON_TIME] + "'", RNS.LOG_VERBOSE)
    RNS.log("- Origin  " + message[MESSAGE_JSON_ORIGIN], RNS.LOG_VERBOSE)
    RNS.log("- Via     " + message[MESSAGE_JSON_ORIGIN], RNS.LOG_VERBOSE)
    if MESSAGE_JSON_PATH in message.keys():
        RNS.log("- Path   " + message[MESSAGE_JSON_PATH], RNS.LOG_VERBOSE)


##########################################################################################
# Nexus LXM router socket for LXMF message handling
#
class NexusLXMSocket:
    # Call back to handle received messages
    message_received_callback = None

    # Class constructor
    def __init__(self, socket_identity=None, storage_path=None, app_name=APP_NAME, server_aspect=NEXUS_SERVER_ASPECT):

        # Initialize members
        self.app_name = app_name
        self.server_aspect = server_aspect

        # If storage path was not set use default storage path
        self.storage_path = storage_path
        if self.storage_path is None:
            self.storage_path = LXMF_STORAGE_PATH
        # Check and create storage path if necessary
        if not os.path.isdir(self.storage_path):
            # Create storage path
            os.makedirs(self.storage_path)
            # Log that storage directory was created
            RNS.log("LXM Storage path was created", RNS.LOG_NOTICE)
        # Log storage path
        RNS.log("LXM Socket storage path is " + self.storage_path, RNS.LOG_INFO)

        # If identity was not given create one for this lxm socket
        self.socket_identity = socket_identity
        if self.socket_identity is None:
            self.socket_identity = RNS.Identity()
        # Log that storage directory was created
        RNS.log("LXM Socket identity is " + str(self.socket_identity), RNS.LOG_DEBUG)

        # Initialize from destination to be used when sending nexus messages to other nexus servers
        self.socket_destination = RNS.Destination(
            self.socket_identity,
            RNS.Destination.IN,
            RNS.Destination.SINGLE,
            self.app_name,
            self.server_aspect
        )
        # Set proof strategy to PROVE_ALL
        self.socket_destination.set_proof_strategy(RNS.Destination.PROVE_ALL)

        # Log the crated lxm destination
        RNS.log("LXM Nexus Server from destination is " + str(self.socket_destination), RNS.LOG_DEBUG)
        RNS.log("LXM Nexus Server hash is " + RNS.prettyhexrep(self.destination_hash()), RNS.LOG_DEBUG)

        # Initialize lxm router
        self.lxm_router = LXMF.LXMRouter(
            identity=self.socket_identity,
            storagepath=self.storage_path
        )
        # Log updated server role
        RNS.log("LXM Router initialized with identity " + str(self.socket_identity), RNS.LOG_DEBUG)

        # Register callback to process incoming links
        self.socket_destination.set_link_established_callback(NexusLXMSocket.client_connected)
        # Log callback for incoming link registered
        RNS.log("LXM Link established callback registered", RNS.LOG_DEBUG)

        # Create a handler to process all incoming announcements with the aspect of this nexus server
        announce_handler = NexusLXMAnnounceHandler(aspect_filter=app_name + '.' + server_aspect)
        # Log announce filter
        RNS.log("LXM AnnounceHandler listens to " + app_name + '.' + server_aspect, RNS.LOG_DEBUG)
        # Register the handler with the reticulum transport layer
        RNS.Transport.register_announce_handler(announce_handler)

        # Flush pending log
        sys.stdout.flush()

    # Register callable to process a received message
    #    handler_function(lxm_message)
    #
    def register_message_received_callback(self, handler_function):
        self.message_received_callback = handler_function

    def destination_hash(self):
        return self.socket_destination.hash

    '''
    def send_lxm_hello(self, destination_hash, announced_identity):
        # Send two test messages to announced nexus server to test LXMF message processing
        # One single packet message
        # One multi packet message
        # This function is not used (demo only) and can be safely removed

        # Send single packet 'Hello World' message
        title = 'Hello Nexus Server'
        content = 'Hello World (Single Packet) - Time: ' + time.ctime(time.time())
        self.send_message(destination_hash, announced_identity, title=title, content=content)

        # Send Multi Packet Hello World message
        title = 'Hello Nexus Server'
        content = 'Hello World (Multi Packet) - Time: ' + time.ctime(time.time()) + \
                  '012345678901234567890123456789012345678901234567890' + \
                  '012345678901234567890123456789012345678901234567890' + \
                  '012345678901234567890123456789012345678901234567890' + \
                  '012345678901234567890123456789012345678901234567890' + \
                  '012345678901234567890123456789012345678901234567890'
        self.send_message(destination_hash, announced_identity, title=title, content=content)
    '''

    def send_message(self, destination_hash, identity, title="", content="", fields=None):
        # Create destination
        to_destination = RNS.Destination(
            identity,
            RNS.Destination.OUT,
            RNS.Destination.SINGLE,
            self.app_name,
            self.server_aspect
        )
        # Create lxmessage and handle outbound to the target Nexus server with the lxm router
        lxm_message = LXMF.LXMessage(
            to_destination,
            destination_hash=destination_hash,
            source=self.socket_destination,
            content=content,
            title=title,
            fields=fields,
            desired_method=LXMF.LXMessage.DIRECT
        )

        # Register message handler
        # This is the good case - message is processed successfully
        lxm_message.register_delivery_callback(NexusLXMSocket.lxmf_delivery_callback)
        # Log delivery failure
        lxm_message.register_failed_callback(NexusLXMSocket.lxmf_delivery_failed_callback)

        # Transfer handling of the message to LXMF
        RNS.log(
            "LXM handle outbound for message sent to " + RNS.prettyhexrep(destination_hash) +
            " from " + RNS.prettyhexrep(self.socket_destination.hash),
            RNS.LOG_VERBOSE
        )
        # Handle outbound
        self.lxm_router.handle_outbound(lxm_message)
        # Give system a moment to process network stuff
        time.sleep(DIGESTION_DELAY)

        # Flush pending log
        sys.stdout.flush()

    ##########################################################################################
    # Announce the server to the reticulum network
    #
    # Calling this function will start a timer that will call this function again after the
    # specified re-announce period.
    #
    @staticmethod
    def announce(initial_announcement=False):
        # Build proper announce data set
        # For the initial announce to trigger subscription linking the timestamp of the latest message is not included.
        # As soon as an announcement from a remote server is received we can safely request a bulk update from it.
        # If the remote server needs an update from this server it can ask for that with the proper identity it has
        # registered already with our first announcement.

        # The announcement contains of:
        # - Server Role
        # - Timestamp of the latest message in the message buffer (in case it is the initial announcement)
        # - Version of this server, command processor and message format used

        # Set nexus default server role as default announce data
        announce_data = NEXUS_SERVER_ROLE

        # Add the latest message time stamp (id) from message buffer except this is the initial announcement
        if not initial_announcement:
            announce_data[ROLE_JSON_LAST] = latest_message_id()
        else:
            # Log that this is the initial announcement
            RNS.log("Preparing the initial Announcement", RNS.LOG_VERBOSE)
        # Add full version dictionary
        announce_data[VERSION_JSON_VERSION] = __full_version__

        # Announce this server to the network
        # All other nexus server with the same aspect will register this server as a distribution target
        NEXUS_LXM_SOCKET.socket_destination.announce(
            # Serialize the nexus server role dict to bytes and set it as app_date to the announcement
            app_data=pickle.dumps(announce_data)
        )
        # Log announcement / long poll announcement
        RNS.log(
            # Log entry does not use bytes but a string representation
            "LXM Nexus Server " + RNS.prettyhexrep(NEXUS_LXM_SOCKET.destination_hash()) +
            " announced with app_data: " + str(announce_data),
            RNS.LOG_INFO
        )

        # Sync message buffer from configured bridges
        sync_from_bridges()

        # Flush pending log
        sys.stdout.flush()

    @staticmethod
    def client_connected(link):
        link.set_resource_strategy(RNS.Link.ACCEPT_ALL)
        RNS.log("LXM Link Resource strategy set to ACCEPT_ALL", RNS.LOG_EXTREME)
        link.set_resource_concluded_callback(NexusLXMSocket.resource_concluded)
        RNS.log("LXM Resource concluded callback set", RNS.LOG_EXTREME)
        link.set_packet_callback(NexusLXMSocket.packet_received)
        RNS.log("LXM Packet callback set", RNS.LOG_EXTREME)

    @staticmethod
    def client_disconnect(link):
        RNS.log("LXM Client disconnected " + str(link), RNS.LOG_EXTREME)
        if link.teardown_reason == RNS.Link.TIMEOUT:
            RNS.log("The link timed out, exiting now", RNS.LOG_EXTREME)
        elif link.teardown_reason == RNS.Link.DESTINATION_CLOSED:
            RNS.log("The link was closed by the server, exiting now", RNS.LOG_EXTREME)
        else:
            RNS.log("Link closed", RNS.LOG_EXTREME)

    @staticmethod
    def packet_received(lxmf_bytes, packet):
        RNS.log("LXM single packet delivered " + str(packet), RNS.LOG_EXTREME)
        # Process received lxmf bytes into a lxmessage
        NexusLXMSocket.process_lxmf_message_bytes(lxmf_bytes)

    @staticmethod
    def resource_concluded(resource):
        RNS.log("LXM Resource data transfer (multi packet) delivered " + str(resource.file), RNS.LOG_EXTREME)
        # Check if transfer is completed
        # otherwise log that it is not
        if resource.status == RNS.Resource.COMPLETE:
            # Read collected parts from the read file handle that came with the resource
            lxmf_bytes = resource.data.read()
            # Process received lxmf bytes into a lxmessage
            NexusLXMSocket.process_lxmf_message_bytes(lxmf_bytes)
        else:
            RNS.log("Received LXMF resource message is not complete", RNS.LOG_EXTREME)

    @staticmethod
    def process_lxmf_message_bytes(lxmf_bytes):
        try:
            # Assemble message object from read bytes
            message = LXMF.LXMessage.unpack_from_bytes(lxmf_bytes)
        except Exception as e:
            RNS.log("Could not assemble LXMF message from received data", RNS.LOG_ERROR)
            RNS.log("The contained exception was: " + str(e), RNS.LOG_ERROR)
            return

        # Log message as delivery receipt
        NexusLXMSocket.log_lxm_message(message, "LXMF Message received")

        # Call message handler if one is registered.
        if NEXUS_LXM_SOCKET.message_received_callback is not None:
            RNS.log("Call to registered message received callback", RNS.LOG_DEBUG)
            NEXUS_LXM_SOCKET.message_received_callback(message)
        else:
            RNS.log("No message received callback registered", RNS.LOG_DEBUG)

    @staticmethod
    def lxmf_delivery_callback(message):
        # Log message as delivery receipt
        NexusLXMSocket.log_lxm_message(message, "LXMF Delivery receipt (success)")

    @staticmethod
    def lxmf_delivery_failed_callback(message):
        # Log message as delivery receipt
        NexusLXMSocket.log_lxm_message(message, "LXMF Delivery receipt (failed)")

    @staticmethod
    def log_lxm_message(message, message_tag="LXMF Message log"):
        # Log Message
        # Create time stamp for logging
        time_string = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(message.timestamp))
        # Check and log signature status
        if message.signature_validated:
            signature_string = "Validated"
        else:
            if message.unverified_reason == LXMF.LXMessage.SIGNATURE_INVALID:
                signature_string = "Invalid signature"
            elif message.unverified_reason == LXMF.LXMessage.SOURCE_UNKNOWN:
                signature_string = "Cannot verify, source is unknown"
            else:
                signature_string = "Signature is invalid, reason undetermined"
        # Log LXM message received event
        title = message.title.decode('utf-8')
        content = message.content.decode('utf-8')
        fields = message.fields
        RNS.log(message_tag + " - " + time_string, RNS.LOG_DEBUG)
        RNS.log("-       Title: " + title, RNS.LOG_DEBUG)
        RNS.log("-     Content: " + content, RNS.LOG_DEBUG)
        RNS.log("-      Fields: " + str(fields), RNS.LOG_DEBUG)
        RNS.log("-        Size: " + str(len(title) + len(content) + len(title) + len(pickle.dumps(fields))) + " bytes",
                RNS.LOG_DEBUG)
        RNS.log("-      Source: " + RNS.prettyhexrep(message.source_hash), RNS.LOG_DEBUG)
        RNS.log("- Destination: " + RNS.prettyhexrep(message.destination_hash), RNS.LOG_DEBUG)
        RNS.log("-   Signature: " + signature_string, RNS.LOG_DEBUG)

    @staticmethod
    def long_poll(initial=False):
        # Announce this server to the network
        # The initial announcement will omit the timestamp of the latest message by setting the initial parameter to
        # True. For all other poll call the timestamp is included in the announcement (role)

        # All other nexus server with the same aspect will register this server as a distribution target
        NEXUS_LXM_SOCKET.announce(initial)

        # Start timer to re announce this server in due time as specified
        t = threading.Timer(NEXUS_SERVER_LONGPOLL, NEXUS_LXM_SOCKET.long_poll)
        # Start as daemon so it terminates with main thread
        t.daemon = True
        t.start()


##########################################################################################
# NexusLXMSocket callback to handle incoming data packets
#
# This function is called as soon as a data packet is received by this server LXM Socket
# Actually all packets are treated as messages.
# ToDo: Implement server commands
#           Digest message
#           Remove message
#           Get messages (since)
#           Get last messages (number of messages)
#
def message_received_callback(lxmessage):
    # Get the 'fields' parameter from the LXM Message and treat them as Nexus Command
    command_result = process_command(lxmessage.fields)

    # Log result of command processing
    if command_result:
        RNS.log("Received LXM Message was successfully processed as Nexus command", RNS.LOG_VERBOSE)
    else:
        RNS.log(
            "LXM Message nexus command processing of " + str(lxmessage.fields) +
            " failed", RNS.LOG_ERROR
        )

    # Flush pending log
    sys.stdout.flush()


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
class NexusLXMAnnounceHandler:
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
        RNS.log("Received an announce from " + RNS.prettyhexrep(destination_hash), RNS.LOG_INFO)

        # Check if we have app data received
        if app_data is None:
            # Log app data missing
            RNS.log("The announce is ignored because it contained no valid nexus role dictionary", RNS.LOG_WARNING)
            return

        # Recreate nexus role dict from received app data
        announced_role = pickle.loads(app_data)
        # Log role
        RNS.log("The announce contained the following nexus role: " + str(announced_role), RNS.LOG_VERBOSE)

        # Validate/Migrate announced role
        if not is_valid_role(validate_role(announced_role)):
            # Log app data missing
            RNS.log("The announce is ignored because it is no valid nexus server role", RNS.LOG_DEBUG)
            return

        # Get dict key and timestamp for distribution identity registration
        last_heard = int(time.time())

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

            # Add update on announce
            # Check if destination is a new destination
            if destination_hash not in DISTRIBUTION_TARGETS.keys():
                new_target = True
            else:
                new_target = False

            # Register/update destination as valid distribution target
            DISTRIBUTION_TARGETS[destination_hash] = (
                last_heard,
                announced_identity,
                announced_role
            )

            # Announce this server if received announcement was a new target
            if new_target:
                # Destination is new
                # Log that we added new subscription
                RNS.log("Subscription " + RNS.prettyhexrep(destination_hash) + " added", RNS.LOG_INFO)
                # Announce this server out of sequence to give accelerate distribution list build up at that new
                # server destination subscription list. This may trigger a bulk update request from that server.
                NexusLXMSocket.announce()
            else:
                # Log that we just updated new subscription
                RNS.log("Subscription " + RNS.prettyhexrep(destination_hash) + " updated", RNS.LOG_INFO)

            # Sync on announce
            # If this announcement is not the first announcement of that server (aka a 'last' key is provided)
            # we ask that server for a bulk update.
            # If this announcement is the first one we wait for the second announcement he sends us after registering us
            # as a new subscription.

            # Check if we have a timestamp
            if ROLE_JSON_LAST in announced_role.keys():
                # Get timestamp (the latest message id) from announcement
                announced_latest = announced_role[ROLE_JSON_LAST]
                actual_latest = latest_message_id()
                # Check ich announced timestamp (the latest message id) indicates an aged local buffer
                if announced_latest > actual_latest:
                    # Request update from remote server
                    update_destination = NEXUS_LXM_SOCKET.destination_hash()
                    cmd = {
                        COMMAND_JSON_CMD: CMD_REQUEST_MESSAGES_SINCE, COMMAND_JSON_VERSION: __command_version__,
                        COMMAND_JSON_P1: actual_latest,
                        COMMAND_JSON_P2: update_destination,
                        COMMAND_JSON_P3: MAXIMUM_UPDATE_MESSAGES
                    }
                    # Log that we are sending a bulk update request to this destination
                    RNS.log(
                        "Send CMD_REQUEST_MESSAGES_SINCE " + str(actual_latest) +
                        " to announced destination " + RNS.prettyhexrep(destination_hash),
                        RNS.LOG_INFO
                    )
                    # Send nexus message packed as lxm message to destination
                    NEXUS_LXM_SOCKET.send_message(
                        destination_hash,
                        announced_identity,
                        fields=cmd
                    )

            # Log list of severs with seconds it was last heard
            for registered_destination_hash in DISTRIBUTION_TARGETS.copy():
                # Get timestamp and destination hash from dict
                timestamp = DISTRIBUTION_TARGETS[registered_destination_hash][0]
                # Calculate seconds since last announce
                last_heard = int(time.time()) - timestamp

                # If destination is expired remove it from dict
                # (This check and cleanup is done at the distribution function as well)
                if last_heard >= NEXUS_SERVER_TIMEOUT:
                    # Log that we removed the destination
                    RNS.log(
                        "Distribution destination " + RNS.prettyhexrep(registered_destination_hash) +
                        " removed because of timeout",
                        RNS.LOG_DEBUG
                    )
                    # Actually remove destination from dict
                    DISTRIBUTION_TARGETS.pop(registered_destination_hash)

                # If actual is still valid log it
                RNS.log(
                    "Registered Server " + RNS.prettyhexrep(registered_destination_hash) +
                    " last heard " + str(last_heard) + "sec ago",
                    RNS.LOG_VERBOSE
                )
        else:
            # Announce should be ignored since it belongs to a different cluster, and we are not eligible to
            # link with that cluster as gateway too
            RNS.log(
                "Announced nexus role was ignored because role did not match role " + str(NEXUS_SERVER_ROLE),
                RNS.LOG_VERBOSE
            )

        # Sync message buffer from configured bridges
        sync_from_bridges()

    # Flush pending log
    sys.stdout.flush()


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

    # Startup log with used parameter
    RNS.log(" ____   _____ ____   _   _                      _____", RNS.LOG_INFO)
    RNS.log("|  _ \\ / ____|  _ \\ | \\ | |                    / ____|", RNS.LOG_INFO)
    RNS.log("| |_) | (___ | |_) ||  \\| | _____  ___   _ ___| (___   ___ _ ____   _____ _ __", RNS.LOG_INFO)
    RNS.log("|  _ < \\___ \\|  _ < | . ` |/ _ \\ \\/ / | | / __|\\___ \\ / _ \\ '__\\ \\ / / _ \\ '__|", RNS.LOG_INFO)
    RNS.log("| |_) |____) | |_) || |\\  |  __/>  <| |_| \\__ \\____) |  __/ |   \\ V /  __/ |", RNS.LOG_INFO)
    RNS.log("|____/|_____/|____(_)_| \\_|\\___/_/\\_\\\\__,_|___/_____/ \\___|_|    \\_/ \\___|_|", RNS.LOG_INFO)
    RNS.log("", RNS.LOG_INFO)
    RNS.log("Copyright (c) 2020 Stephan Becker / Becker-Systemberatung, MIT License", RNS.LOG_INFO)
    RNS.log("...............................................................................", RNS.LOG_INFO)
    RNS.log("Installed Versions:", RNS.LOG_INFO)
    RNS.log(" Nexus Server      v" + __server_version__, RNS.LOG_INFO)
    RNS.log(" Mesh Role         v" + __role_version__, RNS.LOG_INFO)
    RNS.log(" Command Processor v" + __command_version__, RNS.LOG_INFO)
    RNS.log(" Message Format    v" + __message_version__, RNS.LOG_INFO)
    RNS.log("...............................................................................", RNS.LOG_INFO)
    RNS.log("Server Configuration:", RNS.LOG_INFO)
    RNS.log(" Port     " + str(NEXUS_SERVER_ADDRESS[1]), RNS.LOG_INFO)
    RNS.log(" Aspect   " + NEXUS_SERVER_ASPECT, RNS.LOG_INFO)
    RNS.log(" Role     " + str(NEXUS_SERVER_ROLE), RNS.LOG_INFO)
    RNS.log(" Bridge   " + str(BRIDGE_TARGETS), RNS.LOG_INFO)
    RNS.log(" Timeout  " + str(NEXUS_SERVER_TIMEOUT), RNS.LOG_INFO)
    RNS.log(" Longpoll " + str(NEXUS_SERVER_LONGPOLL), RNS.LOG_INFO)
    RNS.log("...............................................................................", RNS.LOG_INFO)

    # Create LXMF router socket with this server as source endpoint
    NEXUS_LXM_SOCKET = NexusLXMSocket()
    # Register callback to handle incoming messages
    NEXUS_LXM_SOCKET.register_message_received_callback(message_received_callback)

    # Load and validate messages from storage
    load_messages()

    # Log http server address/port used
    RNS.log("Serving '" + APP_NAME + '.' + NEXUS_SERVER_ASPECT + "' at %s:%d" % NEXUS_SERVER_ADDRESS, RNS.LOG_INFO)

    RNS.log("Initialization complete", RNS.LOG_INFO)
    RNS.log("...............................................................................", RNS.LOG_INFO)

    # After an initial delay start long poll to announce server regularly
    time.sleep(INITIAL_ANNOUNCEMENT_DELAY)
    NexusLXMSocket.long_poll(initial=True)

    # Launch HTTP GET/POST processing
    # This is an endless loop
    # Termination by ctrl-c or like process termination
    launch_http_server()

    # Flush pending log
    sys.stdout.flush()


##########################################################################################
# Start up of the threaded HTTP server to handle client json GET/POST requests
#
def launch_http_server():
    # Create multithreading http server with given address and port to listen for json app interaction
    httpd = ThreadingHTTPServer(NEXUS_SERVER_ADDRESS, ServerRequestHandler)
    # Invoke server loop
    # (infinite)
    httpd.serve_forever()


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
    # Set headers for actual request
    def _set_success_headers(self):
        # Set response result code and data format
        self.send_response(HTTPStatus.OK)
        self.send_header('Content-type', 'application/json')
        # Allow requests from any origin, so CORS policies don't
        # prevent local development.
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

    def _set_failure_headers(self):
        # Set response result code and data format
        self.send_response(HTTPStatus.NOT_IMPLEMENTED)
        self.send_header('Content-type', 'application/json')
        # Allow requests from any origin, so CORS policies don't
        # prevent local development.
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

    # Simple GET request handler without any URL parameters or request body processing
    # The actual message buffer list is serialized as json string and encoded as bytes.
    # After that it is sent back to the client as the GET request response.
    def do_GET(self):
        self._set_success_headers()
        self.wfile.write(json.dumps(MESSAGE_STORE).encode('utf-8'))

    # Simple POST request handler without any URL parameters and the message to be digested as request body
    # The actual message is decoded into a python map, amended by a timestamp and added to the message store.
    # After that it is sent back to the client as the GET request response.
    def do_POST(self):
        # ToDo: Need to implement more features:
        #    ClearBuffer command
        #    Delete Message command
        #
        # Get length of POST message, read those bytes and parse it as JSON string into a message
        # and append that string to the message store
        length = int(self.headers.get('content-length'))
        body = self.rfile.read(length)

        # Parse JSON
        post = json.loads(body)

        # Log new client message received event
        RNS.log("HTTP POST received with content " + str(post), RNS.LOG_INFO)

        # Try to validate received post as Nexus Command
        command_result = process_command(post)

        # Build result JSON
        result = {'success': command_result}

        # depending on outcome set response header HTTP result value accordingly
        if command_result:
            self._set_success_headers()
            RNS.log("Received HTTP Post was successfully processed as Nexus Command", RNS.LOG_VERBOSE)
        else:
            self._set_failure_headers()
            RNS.log("Received HTTP Post could not be precessed", RNS.LOG_ERROR)
        # Set result JSON to body
        self.wfile.write(json.dumps(result).encode('utf-8'))
        # Log result
        RNS.log("HTTP Post processing result is " + str(result), RNS.LOG_DEBUG)

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
# Process Nexus Server command
#
def process_command(nexus_command):
    # Try to validate command
    command = validate_command(nexus_command)
    if not is_valid_command(command):
        # Try to validate given command as message
        message = validate_message(nexus_command)
        if not is_valid_message(message):
            # Given command was nighter a valid command nor message
            RNS.log("Invalid command " + str(nexus_command), RNS.LOG_ERROR)
            return False
        else:
            # Create proper add_message command from posted message
            RNS.log("WARNING: Deprecated Messaging was processed as ADD_MESSAGE command", RNS.LOG_WARNING)
            command = {
                COMMAND_JSON_CMD: CMD_ADD_MESSAGE, COMMAND_JSON_VERSION: __command_version__,
                COMMAND_JSON_P1: message
            }

    # Prior to executing a command see if we have still some bridges to update from
    sync_from_bridges()

    # Get cmd id from command dict
    cmd = command[COMMAND_JSON_CMD]
    success = False

    # Log start of command processing
    RNS.log("Process command " + str(command), RNS.LOG_VERBOSE)

    # Check if command is add message to buffer command
    if cmd == CMD_ADD_MESSAGE:
        # Retrieve message to add from command dict
        message = command[COMMAND_JSON_P1]
        # Log parsed command
        RNS.log("Process ADD_MESSAGE " + str(message), RNS.LOG_VERBOSE)
        # Process message as message post
        success = cmd_add_message(message)

    # Check if command request sending messages received since a given point in time
    elif cmd == CMD_REQUEST_MESSAGES_SINCE:
        # Retrieve message to add from command dict
        since = command[COMMAND_JSON_P1]
        destination_hash = command[COMMAND_JSON_P2]
        message_count = command[COMMAND_JSON_P3]
        # Log parsed command
        RNS.log(
            "Process REQUEST_MESSAGES_SINCE " + str(since) +
            " from " + RNS.prettyhexrep(destination_hash) +
            " max=" + str(message_count),
            RNS.LOG_VERBOSE
        )
        # Forward messages received to the requested destination
        success = cmd_request_message_since(since, destination_hash, message_count)

    # Command not found
    else:
        # Command processing failed
        RNS.log("Command id " + str(cmd) + " not implemented", RNS.LOG_ERROR)

    # Return result
    return success


##########################################################################################
#
#
def cmd_request_message_since(since, destination_hash, message_count):
    # Check if we have destination already registered
    if destination_hash in DISTRIBUTION_TARGETS.keys():
        # Get destination identity from registered destination
        registered_destination_identity = DISTRIBUTION_TARGETS[destination_hash][1]
        # Init counter and index
        i = 0
        index = len(MESSAGE_STORE) - 1
        # Loop through message buffer
        while i < message_count and index >= 0:
            # Get next most recent message from message store
            message = MESSAGE_STORE[index]
            # Check if message fulfills filter given criteria
            if message[MESSAGE_JSON_ID] >= since:
                # If so send message
                # Assemble Nexus add_message command with message to be sent to requester
                cmd = {
                    COMMAND_JSON_CMD: CMD_ADD_MESSAGE, COMMAND_JSON_VERSION: __command_version__,
                    COMMAND_JSON_P1: message
                }
                # Send nexus message packed as lxm message to destination
                NEXUS_LXM_SOCKET.send_message(
                    destination_hash,
                    registered_destination_identity,
                    fields=cmd
                )
                # Log send message ID
                RNS.log("Message " + str(message[MESSAGE_JSON_ID]) + " sent", RNS.LOG_VERBOSE)
                # Increment message sent counter
                i = i + 1

            # Decrement message store index
            index = index - 1

        # Done sending update
        # Log that we updated the destination
        RNS.log(
            "Destination " + RNS.prettyhexrep(destination_hash) + " has been updated with " + str(i) + " messages",
            RNS.LOG_INFO
        )
        return True
    else:
        # Log that we don't know the destination for this update
        RNS.log(
            "Destination " + RNS.prettyhexrep(destination_hash) + " for message bulk update unknown",
            RNS.LOG_ERROR
        )
        return False


##########################################################################################
# Add Message to Message Buffer
#
def cmd_add_message(message):
    # Check if incoming message was a client sent message and does not have a path tag
    # Bridged messages have a path tag set, local posts of new messages does not.
    if MESSAGE_JSON_PATH not in message.keys():
        # Log new client message received event
        RNS.log("Message to add was send from a client (no path set yet)", RNS.LOG_VERBOSE)
        # ToDo Set message version correctly at client side (actually not implemented in client)
        message[MESSAGE_JSON_VERSION] = __message_version__
        RNS.log("Message version set to " + __message_version__, RNS.LOG_DEBUG)
    else:
        # Log new client message received event
        RNS.log("Message to add was send from a remote server with path " + message[MESSAGE_JSON_PATH], RNS.LOG_VERBOSE)

    # Validate/Migrate message
    message = validate_message(message)
    # Check if message is valid
    if is_valid_message(message):
        # If message has no 'origin' set use this server as origin
        if MESSAGE_JSON_ORIGIN not in message.keys():
            # Set Origin to this server
            message[MESSAGE_JSON_ORIGIN] = RNS.prettyhexrep(NEXUS_LXM_SOCKET.destination_hash())

        # If message has no 'via' set use this server as via
        if MESSAGE_JSON_VIA not in message.keys():
            # Set Via to this server
            message[MESSAGE_JSON_VIA] = RNS.prettyhexrep(NEXUS_LXM_SOCKET.destination_hash())

        # If message has no ID yet create one
        if MESSAGE_JSON_ID not in message.keys():
            # Create a timestamp and add that as ID to the message map
            message[MESSAGE_JSON_ID] = int(time.time() * 100000)

        # Log updated message data
        log_nexus_message(message)

        # Process, store and distribute message as required
        if process_incoming_message(message):
            # Distribute message to all registered or bridged nexus servers
            distribute_message(message)

        # Save message buffer after synchronisation
        save_messages()
        # Return success
        return True

    else:
        # Message failed validation and is ignored
        RNS.log("Message to add failed validation and is ignored", RNS.LOG_ERROR)

        # Return failure
        return False


##########################################################################################
# Post command to remote TCP/IP Nexus peer
#
def post_command(url, cmd):
    # Use POST to send command to TCP/IP nexus peer
    try:
        response = requests.post(
            url=url,
            json=cmd,
            headers={'Content-type': 'application/json'}
        )
        # Check if request was successful
        if response.ok:
            # Log that we bridged a message
            RNS.log("POST request " + url + "' completed successfully", RNS.LOG_VERBOSE)
            # Return success
            return True
        else:
            # Log POST failure
            RNS.log("POST request " + url + "' failed with reason: " + response.reason, RNS.LOG_ERROR)
            # Return failure
            return False

    except Exception as e:
        RNS.log("Could not complete POST request " + url, RNS.LOG_ERROR)
        RNS.log("The contained exception was: %s" % (str(e)), RNS.LOG_ERROR)
        return False


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
        # Validate/Migrate message
        message = validate_message(message)
        # Check if message is valid
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
                "' has invalid version and is dropped",
                RNS.LOG_DEBUG
            )


##########################################################################################
# Process incoming message
#
# This function is called by the nexus add_message command.
# Its Job is to check if we need to add/insert the message in the message buffer or should it be ignored
#
def process_incoming_message(message):
    # If message is more recent than the oldest message in the buffer
    # and has not arrived earlier, then add/insert message at the correct position and
    # Get actual timestamp from message
    message_id = message[MESSAGE_JSON_ID]
    # Get actual number of messages in the buffer
    message_store_size = len(MESSAGE_STORE)

    if message_store_size == 0:
        # First message arrived event
        RNS.log("Message " + str(message_id) + " is first message in the buffer", RNS.LOG_DEBUG)
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
                        " storing and distribution not necessary because message is already in the buffer",
                        RNS.LOG_DEBUG
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
                        " has a duplicate timestamp but differs (Message will be inserted in timeline)",
                        RNS.LOG_DEBUG
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
                RNS.log("Message " + str(message_id) + " will be inserted in timeline", RNS.LOG_DEBUG)
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
                    "Message " + str(message_id) + " is most recent and will be appended to timeline",
                    RNS.LOG_DEBUG
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
                " exceeded. Oldest message is dropped now",
                RNS.LOG_DEBUG
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
def distribute_message(nexus_message):
    # Process bridge targets

    # Loop through all registered bridge targets
    for bridge_target in BRIDGE_TARGETS:
        # Check if actual message was pulled from that target; aka has the same cluster tag like the bridge target
        # Check if we have a cluster tag
        if BRIDGE_JSON_CLUSTER in nexus_message.keys():
            # Check if it is the same as the bridge target
            if nexus_message[BRIDGE_JSON_CLUSTER] == bridge_target[BRIDGE_JSON_CLUSTER]:
                # Log that this message was actually received from that bridge
                RNS.log(
                    "Message distribution to bridge '" + bridge_target[BRIDGE_JSON_CLUSTER] +
                    "' was suppressed because message was received from that bridge",
                    RNS.LOG_VERBOSE
                )
                # Continue with next bridge target
                continue

        # Now lets check if we can find the target cluster in the path of the message
        # If it is there the message has traveled through that cluster already and does not need to go there again
        if nexus_message[MESSAGE_JSON_PATH].find(bridge_target[BRIDGE_JSON_CLUSTER]) != -1:
            # Log that this message was actually received from that bridge
            RNS.log(
                "Message distribution to bridge '" + bridge_target[BRIDGE_JSON_CLUSTER] +
                "' was suppressed because its path '" + nexus_message[MESSAGE_JSON_PATH] +
                "' contains that cluster already",
                RNS.LOG_VERBOSE
            )
            # Continue with next bridge target
            continue

        # Remove cluster tag from message
        if BRIDGE_JSON_CLUSTER in nexus_message.keys():
            nexus_message.pop(BRIDGE_JSON_CLUSTER)

        # Assemble Nexus add_message command for bridge post
        cmd = {
            COMMAND_JSON_CMD: CMD_ADD_MESSAGE, COMMAND_JSON_VERSION: __command_version__,
            COMMAND_JSON_P1: nexus_message
        }
        # Post command to TCP/IP Peer
        result = post_command(bridge_target[BRIDGE_JSON_URL], cmd)
        # Check and log if request was successful
        log_message = "Add message command post to bridge '" + bridge_target[BRIDGE_JSON_CLUSTER]
        if result:
            # Set bridge status to online
            bridge_target[BRIDGE_JSON_ONLINE] = True
            # Log that we bridged a message
            log_message = log_message + "' completed successfully"
        else:
            # Set bridge status to offline
            bridge_target[BRIDGE_JSON_ONLINE] = False
            # Log POST failure
            log_message = log_message + "' failed"
        # Post log entry
        RNS.log(log_message, RNS.LOG_VERBOSE)

    # Process distribution targets

    # Loop through all registered distribution targets
    # Remove all targets that have not announced them self within given timeout period
    # If one target is not expired send message to that target
    for registered_destination_hash in DISTRIBUTION_TARGETS.copy():
        # Get target and identity from target dict
        # Initialize message body
        registered_destination_identity = DISTRIBUTION_TARGETS[registered_destination_hash][1]

        # Back propagation to origin suppression
        # If origin of message to distribute equals target suppress distributing it
        if nexus_message[MESSAGE_JSON_ORIGIN] == RNS.prettyhexrep(registered_destination_hash):
            # Log message received by distribution event
            RNS.log(
                "Distribution to " + RNS.prettyhexrep(registered_destination_hash) +
                " was suppressed because message originated from that server",
                RNS.LOG_VERBOSE
            )
            # Continue with next distribution target
            continue
        # Back propagation to forwarder suppression
        # If forwarder of message to distribute equals target suppress distributing it
        elif nexus_message[MESSAGE_JSON_VIA] == RNS.prettyhexrep(registered_destination_hash):
            # Log message received by distribution event
            RNS.log(
                "Distribution to " + RNS.prettyhexrep(registered_destination_hash) +
                " was suppressed because message was forwarded from that server",
                RNS.LOG_VERBOSE
            )
            # Continue with next distribution target
            continue
        else:
            # Set new forwarder (VIA) id to message
            # Overwrite previous forwarder id
            nexus_message[MESSAGE_JSON_VIA] = RNS.prettyhexrep(NEXUS_LXM_SOCKET.destination_hash())

            # Get time stamp from target dict
            timestamp = DISTRIBUTION_TARGETS[registered_destination_hash][0]
            # Get actual time from system
            actual_time = int(time.time())

            # Check if target has not expired yet
            if (actual_time - timestamp) < NEXUS_SERVER_TIMEOUT:
                # Assemble Nexus add_message command for lxm transport
                cmd = {
                    COMMAND_JSON_CMD: CMD_ADD_MESSAGE, COMMAND_JSON_VERSION: __command_version__,
                    COMMAND_JSON_P1: nexus_message
                }
                # Send nexus message packed as lxm message to destination
                NEXUS_LXM_SOCKET.send_message(
                    registered_destination_hash,
                    registered_destination_identity,
                    fields=cmd
                )
                # Log that we send something to this destination
                RNS.log(
                    "Message sent to destination " + RNS.prettyhexrep(registered_destination_hash),
                    RNS.LOG_VERBOSE
                )
            else:
                # Log that we removed the destination
                RNS.log(
                    "Distribution destination " + RNS.prettyhexrep(registered_destination_hash) + " removed",
                    RNS.LOG_VERBOSE
                )
                # Remove expired target identity from distribution list
                DISTRIBUTION_TARGETS.pop(registered_destination_hash)


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
