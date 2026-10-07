"""A tiny local server whose GET /slow?ms=N answers with a 1x1 GIF after N ms. A page that adds <img src=".../slow?ms=12000">
keeps its load event (and so headless Edge's --dump-dom) waiting that long, which lets OfflineAudioContext renders finish.
Usage: python slowserver.py [port] [lifetime seconds]; it shuts itself down after the lifetime."""
import http.server
import socketserver
import sys
import threading
import time
from urllib.parse import parse_qs, urlparse

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8799
LIFE = int(sys.argv[2]) if len(sys.argv) > 2 else 180
GIF = (b'GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00'
       b'\x01\x00\x00\x02\x02D\x01\x00;')


class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        q = parse_qs(urlparse(self.path).query)
        time.sleep(int(q.get('ms', ['1000'])[0]) / 1000)
        self.send_response(200)
        self.send_header('Content-Type', 'image/gif')
        self.send_header('Content-Length', str(len(GIF)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(GIF)

    def log_message(self, *a):
        pass


class S(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = True


srv = S(('127.0.0.1', PORT), H)
threading.Timer(LIFE, srv.shutdown).start()
srv.serve_forever()
