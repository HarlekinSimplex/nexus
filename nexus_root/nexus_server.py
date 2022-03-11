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
#]

messageStore = [
]


MESSAGE_BUFFER_SIZE = 20
DEBUG = False


class _RequestHandler(BaseHTTPRequestHandler):

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
        message['id'] = int(time.time()*100000)

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


def run_server():
    server_address = ('', 4281)
    httpd = ThreadingHTTPServer(server_address, _RequestHandler)
    print('serving at %s:%d' % server_address)
    httpd.serve_forever()


if __name__ == '__main__':
    run_server()
