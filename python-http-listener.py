#!/usr/bin/env python3
from http.server import BaseHTTPRequestHandler, HTTPServer

class SimpleHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get('content-length', 0))
        body = self.rfile.read(length) if length > 0 else b''

        print("\n--- Incoming Request ---")
        print("Path:", self.path)
        print("Method:", self.command)
        print("Headers:\n", self.headers)
        print("Body:", body.decode(errors="replace"))
        print("------------------------\n")

        # Отговор 200 OK
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"OK")

    # Ако искаш да реагира и на GET:
    def do_GET(self):
        print("\n--- Incoming GET ---")
        print("Path:", self.path)
        print("Headers:\n", self.headers)
        print("---------------------\n")

        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"OK")

def run():
    server = HTTPServer(("127.0.0.1", 8008), SimpleHandler)
    print("Listening on http://127.0.0.1:8008 ...")
    server.serve_forever()

if __name__ == "__main__":
    run()
