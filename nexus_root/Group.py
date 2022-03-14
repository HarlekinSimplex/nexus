###########################################################
# This RNS example demonstrates usage off Group encrypted #
# communication                                           #
###########################################################

import sys
import argparse
import RNS

# Let's define an app name. We'll use this for all
# destinations we create. Since this basic example
# is part of a range of example utilities, we'll put
# them all within the app namespace "example_utilities"
APP_NAME = "example_utilities"


# This initialisation is executed when the program is started
def program_setup(configpath, group=None, key=None):
    # We must first initialise Reticulum
    reticulum = RNS.Reticulum(configpath)

    # If the user did not select a "group" we use
    # a default one called "demo_group".
    # This "group" is added to the destination name-
    # space, so the user can select different groups.
    if group is None:
        group = "demo_group"

    # We create a PLAIN destination. This is an unencrypted endpoint
    # that anyone can listen to and send information to.
    group_destination = RNS.Destination(
        None,
        RNS.Destination.IN,
        RNS.Destination.GROUP,
        APP_NAME,
        "group",
        group
    )

    # Just a 'public' key for debug purpose or to use form public but encrypted broadcasts with a known key
    #    key = b'jC\xac\xcb\x04jaig\xd0\xda\x13Au\x95\xb1c=id\xc7\x10\xad\xf6(\xf0?\x8e\xf9d<9'
    #    key = b'12345678901234567890123456789012'
    #    key = b'TheQuickBrownFoxJumpsOverTheLazy'
    key = b'ReticulumWasDevelopedByMarkQvist'

    # If the user did not set a key we create a new key. and
    # Otherwise, we use the provided key
    if key is None:
        group_destination.create_keys()
    else:
        group_destination.load_private_key(key)

    # Log the actually used group key to the console
    print("Symmetric key for group <" + group + "> is <" + str(group_destination.get_private_key()) + ">")

    # We specify a callback that will get called every time
    # the destination receives data.
    group_destination.set_packet_callback(packet_callback)

    # Everything's ready!
    # Let's hand over control to the main loop
    groupLoop(group_destination)


def packet_callback(data, packet):
    # Simply print out the received data
    print("")
    print("Received data: " + data.decode("utf-8") + "\r\n> ", end="")
    sys.stdout.flush()


def groupLoop(destination):
    # Let the user know that everything is ready
    RNS.log(
        "Group example " +
        RNS.prettyhexrep(destination.hash) +
        " running, enter text and hit enter to send to group (Ctrl-C to quit)"
    )

    # We enter a loop that runs until the users exits.
    # If the user hits enter, we will send the information
    # that the user entered into the prompt.
    while True:
        print("> ", end="")
        entered = input()

        if entered != "":
            data = entered.encode("utf-8")
            packet = RNS.Packet(destination, data)
            packet.send()


#######################################################
# Program Startup #####################################
#######################################################

# This part of the program gets run at startup,
# and parses input from the user, and then starts
# the program.
if __name__ == "__main__":
    try:
        parser = argparse.ArgumentParser(
            description="Reticulum example demonstrating sending to and receiving from a group"
        )

        parser.add_argument(
            "--config",
            action="store",
            default=None,
            help="path to alternative Reticulum config directory",
            type=str
        )

        parser.add_argument(
            "--group",
            action="store",
            default=None,
            help="group name",
            type=str
        )

        parser.add_argument(
            "--key",
            action="store",
            default=None,
            help="group symmetric key",
            type=str
        )

        args = parser.parse_args()

        if args.config:
            configarg = args.config
        else:
            configarg = None

        if args.group:
            grouparg = args.group
        else:
            grouparg = None

        if args.key:
            keyarg = args.key
        else:
            keyarg = None

        program_setup(configarg, grouparg, keyarg)

    except KeyboardInterrupt:
        print("")
        exit()
