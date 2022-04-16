import os
import RNS
import LXMF
import time

APP_NAME = "nexus"
NEXUS_SERVER_ASPECT = "cockpit"

# Message storage
MESSAGE_STORAGE_PATH = os.path.expanduser("~") + "/.nexus/storage"
MESSAGE_STORAGE_FILE = MESSAGE_STORAGE_PATH + "/messages.umsgpack"
# LXMF storage
LXMF_STORAGE_PATH = os.path.expanduser("~") + "/.nexus/lxmf"

RNS.Reticulum()

if not os.path.isdir(LXMF_STORAGE_PATH):
    # Create storage path
    os.makedirs(LXMF_STORAGE_PATH)
    # Log that storage directory was created
    RNS.log("Storage path was created")
# Log storage path
RNS.log("Storage path is " + LXMF_STORAGE_PATH)

key = b'\xab/\x91\x02t\xae\xe5\xa1-\xf3\xc9\xf8\xcd\x06\x0b\\\xfa\xcddU\t\xc3O\xa5\x93gH\xe61\xad\xa4 '

destination_to1 = RNS.Destination(
    None, RNS.Destination.IN, RNS.Destination.GROUP, APP_NAME, NEXUS_SERVER_ASPECT
)
destination_to1.load_private_key(key)

destination_to2 = RNS.Destination(
    None, RNS.Destination.IN, RNS.Destination.GROUP, APP_NAME, NEXUS_SERVER_ASPECT
)
destination_to2.load_private_key(key)

destination_from = RNS.Destination(
    RNS.Identity(), RNS.Destination.OUT, RNS.Destination.SINGLE, APP_NAME, NEXUS_SERVER_ASPECT
)

destination_from.announce()

RNS.log("Destination To1 is " + str(destination_to1))
RNS.log("Destination To1 Hash is " + RNS.prettyhexrep(destination_to1.hash))
RNS.log("Destination To2 is " + str(destination_to2))
RNS.log("Destination To2 Hash is " + RNS.prettyhexrep(destination_to2.hash))
RNS.log("Destination From is " + str(destination_from))
RNS.log("Destination From Hash is " + RNS.prettyhexrep(destination_from.hash))

message_text = "Test content"
message_title = "Test Title"

lxmessage = LXMF.LXMessage(
    destination=destination_to1,
    source=destination_from,
    content=message_text,
    title=message_title,
    desired_method=LXMF.LXMessage.DIRECT
    # desired_method=LXMF.LXMessage.OPPORTUNISTIC
)

lxrouter = LXMF.LXMRouter(storagepath=LXMF_STORAGE_PATH)
lxrouter.handle_outbound(lxmessage)

while True:
    time.sleep(1)
