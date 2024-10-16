import socket
import threading
import json

# maintaining clients and connections/states
clients = {}

# initial server setup
def handle_client(client_socket, client_address):
    print(f"New connection from {client_address}")
    client_socket.sendall(b"Welcome to Shippy!")
    
    while True:
        try:
            # receive data from client
            message = client_socket.recv(1024)
            if not message:
                break
            
            message = json.loads(message.decode())
            message_type = message.get("type")

            if message_type == "join":
                handle_join(client_socket, client_address)
            # TODO: move/place functionality
            # TODO: target functionality
            # TODO: chat functionality
            elif message_type == "quit":
                handle_quit(client_socket, client_address)
                break
            else:
                client_socket.sendall(b"Invalid message type")

        except (socket.error, socket.timeout) as e:
            print(f"Error with client {client_address}: {e}")
            break

    # disconnect
    client_socket.close()
    remove_client(client_address)

def handle_join(client_socket, client_address):
    # add client to the game
    clients[client_address] = {'socket': client_socket, 'game_state': {}}
    broadcast_message({"type": "info", "message": f"{client_address} joined the game."})

def handle_quit(client_socket, client_address):
    # remove client from the game
    client_socket.sendall(b"Quitting game")
    broadcast_message({"type": "info", "message": f"{client_address} left the game."})

def broadcast_message(message):
    for client in clients.values():
        try:
            client['socket'].sendall(json.dumps(message).encode())
        except socket.error as e:
            print(f"Failed to send to client: {e}")

def remove_client(client_address):
    if client_address in clients:
        del clients[client_address]

def start_server(tcp_port=12358):
    server_ip = "0.0.0.0"
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((server_ip, tcp_port))
    server_socket.listen(5)
    
    print(f"Server started on {server_ip}:{tcp_port}")

    try:
        while True:
            # accept new client connections
            client_socket, client_address = server_socket.accept()
            
            # log new connection and handle in new thread
            print(f"Accepted connection from {client_address}")
            client_handler = threading.Thread(target=handle_client, args=(client_socket, client_address))
            client_handler.start()

    except KeyboardInterrupt:
        print("\nServer is shutting down...")
    finally:
        server_socket.close()

if __name__ == "__main__":
    start_server()