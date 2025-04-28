### variant 1 ###
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import threading

class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Process the request
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        
        # Generate response
        response = f"Hello! You requested: {self.path}\n"
        self.wfile.write(response.encode('utf-8'))
        
        # Connection will be closed automatically

def run_server(port=8000):
    server_address = ('', port)
    httpd = ThreadingHTTPServer(server_address, SimpleHandler)
    print(f"Server running on port {port}")
    httpd.serve_forever()

if __name__ == '__main__':
    # Start the server in a separate thread
    server_thread = threading.Thread(target=run_server)
    server_thread.daemon = True
    server_thread.start()
    
    # Main thread can continue doing other things
    try:
        while True:
            pass
    except KeyboardInterrupt:
        print("\nShutting down server...")
        exit(0)

### variant 2 ###
from socketserver import ThreadingTCPServer, BaseRequestHandler
import threading

class SimpleTCPHandler(BaseRequestHandler):
    def handle(self):
        # Receive data
        data = self.request.recv(1024).decode('utf-8').strip()
        print(f"Received: {data}")
        
        # Generate response
        response = f"ECHO: {data}\n"
        self.request.sendall(response.encode('utf-8'))
        # Connection closes automatically when handler completes

def run_server(port=8000):
    with ThreadingTCPServer(('', port), SimpleTCPHandler) as server:
        print(f"TCP Server running on port {port}")
        server.serve_forever()

if __name__ == '__main__':
    server_thread = threading.Thread(target=run_server)
    server_thread.daemon = True
    server_thread.start()
    
    try:
        while True:
            pass
    except KeyboardInterrupt:
        print("\nServer shutting down...")

### variant 3 ###
import socket
import select

HOST = '0.0.0.0'  # Listen on all interfaces
PORT = 12345      # Choose your port

# Create TCP socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind((HOST, PORT))
server_socket.listen()

# Set the socket to non-blocking mode
server_socket.setblocking(False)

# List of sockets to monitor for incoming connections
sockets_list = [server_socket]

print(f"Listening on {HOST}:{PORT}...")

while True:
    # Use select to wait for socket activity
    read_sockets, _, exception_sockets = select.select(sockets_list, [], sockets_list)

    for notified_socket in read_sockets:
        if notified_socket == server_socket:
            # New connection
            client_socket, client_address = server_socket.accept()
            client_socket.setblocking(False)
            sockets_list.append(client_socket)
            print(f"Accepted connection from {client_address}")
        else:
            try:
                # Existing connection
                data = notified_socket.recv(1024)
                if data:
                    print(f"Received data: {data.decode().strip()}")
                    response = b"Hello, World!\n"
                    notified_socket.sendall(response)
                # Close after response
                sockets_list.remove(notified_socket)
                notified_socket.close()
            except Exception as e:
                print(f"Error: {e}")
                sockets_list.remove(notified_socket)
                notified_socket.close()

    for notified_socket in exception_sockets:
        sockets_list.remove(notified_socket)
        notified_socket.close()
