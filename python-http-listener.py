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

curl -X POST http://127.0.0.1:8008/hello/world -d "hello"


#!/usr/bin/env python3
from http.server import BaseHTTPRequestHandler, HTTPServer

class H(BaseHTTPRequestHandler):
    def do_POST(self):
        l = int(self.headers.get("content-length", 0))
        body = self.rfile.read(l).decode()
        print(self.command, self.path, body)
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

server = HTTPServer(("127.0.0.1", 8008), H)
server.serve_forever()


#!/usr/bin/env python3
from aiohttp import web

async def handler(request):
    body = await request.text()
    print("\n--- Async Request ---")
    print("Path:", request.path)
    print("Method:", request.method)
    print("Headers:", request.headers)
    print("Body:", body)
    print("----------------------\n")
    return web.Response(text="OK")

app = web.Application()
app.router.add_route("*", "/mqtt", handler)

web.run_app(app, host="127.0.0.1", port=8008)

from http.server import BaseHTTPRequestHandler, HTTPServer

class H(BaseHTTPRequestHandler):
    def do_POST(self):
        l = int(self.headers.get("content-length", 0))
        body = self.rfile.read(l).decode()
        print(self.command, self.path, body)
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

server = HTTPServer(("127.0.0.1", 8008), H)
server.serve_forever()


#!/usr/bin/env python3
from aiohttp import web

async def h(req):
    print(req.method, req.path, await req.text())
    return web.Response(text="OK")

app = web.Application()
app.router.add_route("*", "/mqtt", h)
web.run_app(app, host="127.0.0.1", port=8008)


#!/usr/bin/env python3
import asyncio

async def handle(reader, writer):
    data = await reader.read(65535)
    print("\n--- RAW REQUEST ---")
    print(data.decode(errors="ignore"))
    print("-------------------\n")

    resp = b"HTTP/1.1 200 OK\r\nContent-Length: 2\r\n\r\nOK"
    writer.write(resp)
    await writer.drain()
    writer.close()

async def main():
    server = await asyncio.start_server(handle, "127.0.0.1", 8008)
    async with server:
        await server.serve_forever()

asyncio.run(main())


#!/usr/bin/env python3
from fastapi import FastAPI, Request
import uvicorn

app = FastAPI()

@app.api_route("/mqtt", methods=["GET", "POST"])
async def mqtt(req: Request):
    body = await req.body()
    print(req.method, req.url.path, body.decode())
    return "OK"

uvicorn.run(app, host="127.0.0.1", port=8008)


#!/usr/bin/env node
const http = require("http");

http.createServer((req, res) => {
  let body = "";
  req.on("data", chunk => body += chunk);
  req.on("end", () => {
    console.log(req.method, req.url, body);
    res.writeHead(200, {"Content-Type": "text/plain"});
    res.end("OK");
  });
}).listen(8008, "127.0.0.1");


#!/usr/bin/bash
while true; do
  { 
    echo -e "HTTP/1.1 200 OK\r\nContent-Length: 2\r\n\r\nOK";
  } | nc -l 127.0.0.1 8008
done
