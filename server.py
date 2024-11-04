import socket
import threading
import json
import numpy
import uuid;

# maintaining clients and connections/states
clients = {}

# additional global variables for turn management
players = []  # List to hold connected players
current_turn_index = 0  # Index to track whose turn it is

# setting max amount of ships
MAX_SHIPS = 5

# updating game state after every move
def broadcast_game_state():
    """Broadcast the current game state to all connected clients."""
    game_state_message = {
        "type": "game_state",
        "clients": {str(addr): {
            'ships': data['game_state']['ships'],
            'targets': data['game_state']['targets'].tolist()  # Convert numpy array to list
        } for addr, data in clients.items()}
    }
    broadcast_message(game_state_message)

# initial server setup
def handle_client(client_socket, client_address):
    print(f"New connection from {client_address}")
    client_socket.sendall(b"Welcome to Shippy!")
    
    while True:
        try:
            # receive data from client
            message = client_socket.recv(4096)
            if not message:
                break
            
            # Parse the received message
            message = json.loads(message.decode())
            message_type = message.get("type")

            if message_type == "join":
                handle_join(client_socket, client_address, message)  # Pass 'message' to handle_join()
            # TODO: move/place functionality
            elif message_type == "place":
                handle_place(client_socket, client_address, message)
            elif message_type == "target":
                handle_target(client_socket, client_address, message)
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


def handle_join(client_socket, client_address, response_data):
    # Create a unique ID for the player
    player_id = str(uuid.uuid4())

    try:
        # Use the received response_data directly
        username = response_data.get("username", f"Player_{player_id[:4]}")  # Default to 'Player_<ID>' if not provided

        # Debugging: print received data
        print(f"Received join request from {client_address} with data: {response_data}")

    except (json.JSONDecodeError, ValueError) as e:
        print(f"Error handling join request from {client_address}: {e}")
        client_socket.sendall((json.dumps({"type": "error", "message": "Invalid or empty join request."}) + "\n").encode())
        return

    # Add client to the game
    game_state = {
        'ships': [],
        'targets': numpy.full((10, 10), '^', dtype=object)
    }

    clients[client_address] = {
        'socket': client_socket,
        'game_state': game_state,
        'id': player_id,
        'username': username
    }

    # Add the player to the global list of players
    players.append({'id': player_id, 'username': username, 'socket': client_socket})

    # Send player ID and username back to the client for reference
    print(f"Sending join response to {client_address}")
    client_socket.sendall((json.dumps({"type": "id", "player_id": player_id, "username": username}) + "\n").encode())

    # Broadcast that a new player has joined and update the game state
    broadcast_message({"type": "info", "message": f"{username} ({player_id}) joined the game."})
    broadcast_game_state()  # Ensure the updated game state is broadcasted to all clients



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
    client_socket.sendall((json.dumps({"type": "info", "message": f"Ship placed at {ship_position}."}) + "\n").encode())

    # broadcast updated game state after placement
    broadcast_game_state()

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

    # broadcast updated game state after targeting
    broadcast_game_state()

def handle_chat(client_address, message):
    broadcast_message({"type": "info", "message": message.get("message")})
    print(f"Client {client_address} sent a chat: {message.get("message")}")

def handle_quit(client_socket, client_address):
    # remove client from the game
    broadcast_message({"type": "info", "message": f"{client_address} left the game."})
    print(f"Client {client_address} left the game")

    # broadcast updated game state after a player leaves
    broadcast_game_state()

def broadcast_message(message):
    disconnected_clients = []
    for client_addr, client_data in clients.items():
        try:
            # Send message with a newline delimiter to mark the end of the message
            client_data['socket'].sendall((json.dumps(message) + "\n").encode())
        except socket.error as e:
            print(f"Failed to send to client {client_addr}: {e}")
            disconnected_clients.append(client_addr)

    # Remove disconnected clients
    for client_addr in disconnected_clients:
        remove_client(client_addr)

    # Notify other clients about the disconnections
    for client_addr in disconnected_clients:
        print(f"Client {client_addr} has been removed due to disconnection.")
        broadcast_game_state()  # Broadcast the updated game state after client disconnection




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
