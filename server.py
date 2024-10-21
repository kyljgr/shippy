import socket
import threading
import json
import numpy

# maintaining clients and connections/states
clients = {}

# setting max amount of ships
MAX_SHIPS = 5

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
            elif message_type == "place":
                handle_place(client_socket, client_address, message)
            # TODO: target functionality
            elif message_type == "target":
                handle_target(client_socket, client_address, message)
            # TODO: chat functionality
            elif message_type == "chat":
                handle_chat(client_address, message)
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
    game_state = {
        'ships': [], 
        'targets': numpy.full((10, 10), '^', dtype=object)
    }
    clients[client_address] = {'socket': client_socket, 'game_state': game_state}
    broadcast_message({"type": "info", "message": f"{client_address} joined the game."})

def handle_place(client_socket, client_address, message):
    # ensure client has joined the game (sanity check lol)
    client_data = clients.get(client_address)
    if not client_data:
        client_socket.sendall(json.dumps({"type": "error", "message": "You must join first."}).encode())
        return

    ships = client_data['game_state']['ships']
    if len(ships) >= MAX_SHIPS:
        client_socket.sendall(json.dumps({"type": "error", "message": "Maximum ships placed."}).encode())
        return

    # extract ship placement from message
    ship_position = message.get("position")
    if not ship_position:
        client_socket.sendall(json.dumps({"type": "error", "message": "Invalid position."}).encode())
        return

    # add ship to client's game state
    ships.append(ship_position)
    
    # output to server where the ship was placed
    print(f"Client {client_address} placed a ship at {ship_position}. Total ships for this player: {len(ships)}")
    
    # send confirmation back to the client
    client_socket.sendall(json.dumps({"type": "info", "message": f"Ship placed at {ship_position}."}).encode())

def handle_target(client_socket, client_address, message):
    # ensure client has joined the game (sanity check lol)
    client_data = clients.get(client_address)
    if not client_data:
        client_socket.sendall(json.dumps({"type": "error", "message": "You must join first."}).encode())
        return
    
    # ensure target cell has not already been targeted
    coord_pair = message.get("target")
    # numerical axis
    x_coord = int(coord_pair[1:]) - 1
    # alphabetical axis converted from A-J to 1-10 for indexing
    y_coord = ord(coord_pair[0].upper()) - ord('A')
    target = client_data['game_state']['targets'][x_coord, y_coord]
    if target == '*':
        client_socket.sendall(json.dumps({"type": "error", "message": "You have already targeted this location."}).encode())
        return

    # ensure all ships have been placed first
    ships = client_data['game_state']['ships']
    if len(ships) != MAX_SHIPS:
        client_socket.sendall(json.dumps({"type": "error", "message": "You must place all of your ships first."}).encode())
        return

    #TODO: Signal when a ship is hit by comparing ship locations with targeted cell

    # update target matrix with newly targeted cell
    client_data['game_state']['targets'][x_coord, y_coord] = "*"

    # output to server the cell that was targeted
    print(f"Client {client_address} targeted {coord_pair}")
    
    # send confirmation back to the client
    #TODO: if target was a hit specify. if not specify
    broadcast_message({"type": "info", "message": f"{client_address} fired on {coord_pair}."})

def handle_chat(client_address, message):
    broadcast_message({"type": "info", "message": message.get("message")})
    print(f"Client {client_address} sent a chat: {message.get("message")}")

def handle_quit(client_socket, client_address):
    # remove client from the game
    broadcast_message({"type": "info", "message": f"{client_address} left the game."})
    print(f"Client {client_address} left the game")

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
