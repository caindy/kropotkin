# Copyright Douglas Squirrel 2011
# This program comes with ABSOLUTELY NO WARRANTY. 
# It is free software, and you are welcome to redistribute it under certain conditions; see the GPLv3 license in the file LICENSE for details.

import messageboard, json, urlparse
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer

class HTTPHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        incoming_key = 'http_GET%s' % urlparse.urlparse(self.path).path.replace('/','.')
        request_id = 9999 
        mb = messageboard.MessageBoard()
        queue = mb.watch_for(keys=["%s.%s" % (incoming_key, request_id)])
        mb.post(key=incoming_key, content={'request_id': request_id})
        key, content = mb.get_one_message(queue)
        response = content['response'] if content else None

        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(response))
        return

try:
    mb = messageboard.MessageBoard()    
    server = HTTPServer(('', 8080), HTTPHandler)
    mb.post(key='process_ready.http_server')
    server.serve_forever()
except KeyboardInterrupt:
    server.socket.close()


