import http.server
import socketserver
import sys

class Handler(http.server.SimpleHTTPRequestHandler):
    def handle_auth_fail(self):
        if "auth-fail" in self.path:
            self.send_response(401)
            self.end_headers()
            self.wfile.write(b"Authentication failed")
            return True
        return False

    def do_GET(self):
        if self.handle_auth_fail(): return
        super().do_GET()

    def do_HEAD(self):
        if self.handle_auth_fail(): return
        super().do_HEAD()

if __name__ == "__main__":
    port = int(sys.argv[1])
    directory = sys.argv[2]
    
    class DualHandler(Handler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=directory, **kwargs)

    with socketserver.TCPServer(("", port), DualHandler) as httpd:
        httpd.serve_forever()
