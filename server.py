import socket
import threading

# initial server setup
def handle_client(client_socket, client_address):
    print(f"New connection from {client_address}")
    client_socket.sendall(b"Welcome to the server!")
    
    while True:
        try:
            # receive data from client
            message = client_socket.recv(1024)
            if not message:
                break
            
            # log received message and send acknowledgment back
            print(f"Received from {client_address}: {message.decode()}")
            client_socket.sendall(b"Message received")

        except (socket.error, socket.timeout) as e:
            print(f"Error with client {client_address}: {e}")
            break

    # log the disconnect
    print(f"Connection with {client_address} closed")
    client_socket.close()

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