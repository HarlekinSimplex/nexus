import os
import sys
import signal
import time

from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from http import HTTPStatus

import RNS
import LXMF

LOG_CRITICAL = 0
LOG_ERROR = 1
LOG_WARNING = 2
LOG_NOTICE = 3
LOG_INFO = 4
LOG_VERBOSE = 5
LOG_DEBUG = 6
LOG_EXTREME = 7
loglevel = LOG_EXTREME


def __do_something():
    # Pull up Reticulum stack as configured
    RNS.Reticulum()

    lxm_storage = os.path.expanduser("~") + "/.nexus/storage_lxm"
    if not os.path.isdir(lxm_storage):
        # Create storage path
        os.makedirs(lxm_storage)
        # Log that storage directory was created
        RNS.log("Created storage path " + lxm_storage)

    lxm_router = LXMF.LXMRouter(storagepath=lxm_storage)
    lxm_router.register_delivery_callback(lxmf_delivery_callback)

    identity_a = RNS.Identity()
    identity_b = RNS.Identity()

    source = RNS.Destination(
        identity_a,
        RNS.Destination.OUT,
        RNS.Destination.SINGLE,
        "nexus",
        "cockpit"
    )
    RNS.log("source full address: " + str(source))
    RNS.log("source address (hash): " + RNS.prettyhexrep(source.hash))
    source.announce()

    destination = RNS.Destination(
        identity_b,
        RNS.Destination.IN,
        RNS.Destination.SINGLE,
        "nexus",
        "cockpit"
    )
    RNS.log("destination full address: " + str(destination))
    RNS.log("destination address (hash): " + RNS.prettyhexrep(destination.hash))
    destination.announce()

    lxm_message = LXMF.LXMessage(destination, source, "Content String A->B", "Title Sting")
    lxm_router.handle_outbound(lxm_message)

    launch_http_server()


# noinspection DuplicatedCode
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

    RNS.log(
        "Received LXMF Package " + time_string + " " + signature_string
    )


def launch_http_server():
    httpd = ThreadingHTTPServer(('', 4380), ServerRequestHandler)
    httpd.serve_forever()


class ServerRequestHandler(BaseHTTPRequestHandler):
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

    def do_POST(self):
        pass

    def do_OPTIONS(self):
        self.send_response(HTTPStatus.NO_CONTENT)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST')
        self.send_header('Access-Control-Allow-Headers', 'content-type')
        self.end_headers()


def signal_handler(_signal, _frame):
    print("exiting")
    RNS.exit()

    # Flush pending log
    sys.stdout.flush()
    # Exit
    sys.exit(0)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)

    # Parse commandline arguments
    try:

        __do_something()
        launch_http_server()

    # Handle keyboard interrupt aka ctrl-C to exit server
    except KeyboardInterrupt:
        print("Server terminated by ctrl-c")

        # Flush pending log
        sys.stdout.flush()
        sys.exit(0)
