import socket
import threading
import json
import numpy
import sys

# maintaining clients and connections/states
clients = {}

# setting max amount of ships
MAX_SHIPS = 5

# initial server setup
def handle_client(client_socket, client_address):
    # Give player id to 1st or 2nd player to join
    client_id = getClientID()
    print(f"New connection from {client_address}")
    client_socket.sendall(json.dumps({"player": f"{client_id}", "message": f"Welcome to Shippy!"}).encode())
    
    while True:
        try:
            # receive data from client
            message = client_socket.recv(1024)
            if not message:
                break
            
            message = json.loads(message.decode())
            message_type = message.get("type")

            if message_type == "join":
                handle_join(client_socket, client_address, client_id)
            # TODO: move/place functionality
            elif message_type == "place":
                handle_place(client_socket, client_address, message, client_id)
            # TODO: target functionality
            elif message_type == "target":
                handle_target(client_socket, client_address, message, client_id)
            # TODO: chat functionality
            elif message_type == "chat":
                handle_chat(client_address, message, client_id)
            elif message_type == "quit":
                handle_quit(client_socket, client_address, client_id)
                break
            else:
                client_socket.sendall(b"Invalid message type")

        except (socket.error, socket.timeout) as e:
            print(f"Error with client {client_address}: {e}")
            break

    # disconnect
    client_socket.close()
    remove_client(client_address)
    print(f"Closed connection to client {client_address}...")

def getClientID():
    for id in clients:
        if id.get('client_id') == "Player 1":
            return "Player 2"
        else:
            return "Player 1"

def handle_join(client_socket, client_address, client_id):
    # game state dictionary
    game_state = {
        'ships': [],
        'targets': [],
        'ship_positions': numpy.full((10, 10), '~', dtype=object),
        'target_positions': numpy.full((10, 10), '~', dtype=object)
    }
    # add client to the game
    clients[client_address] = {'socket': client_socket, 'address': client_address, 'game_state': game_state, 'client_id': client_id}
    broadcast_message({"type": "join_response", "player": f"{client_id}", "message": f"{client_id} joined the game."})
    
def handle_place(client_socket, client_address, message, client_id):
    # ensure client has joined the game (sanity check lol)
    client_data = clients.get(client_address)
    if not client_data:
        client_socket.sendall(json.dumps({"type": "error_response", "player": f"{client_id}", "message": "You must join first."}).encode())
        return

    ships = client_data['game_state']['ships']
    if len(ships) >= MAX_SHIPS:
        client_socket.sendall(json.dumps({"type": "error_response", "player": f"{client_id}", "message": "Maximum ships placed."}).encode())
        return

    # extract ship placement from message
    ship_position = message.get("position").upper()

    # parse coordinates
    x_coord = int(ship_position[1:]) - 1  # numerical axis
    y_coord = ord(ship_position[0].upper()) - ord('A')  # alphabetical axis converted from A-J to 1-10 for indexing

    # ensure there is enough room for a 3-length ship
    if x_coord + 2 >= 10:
        client_socket.sendall(json.dumps({"type": "error_response", "player": f"{client_id}", "message": "Not enough room for ship."}).encode())
        return

    # ensure the cells are not already occupied
    ship_matrix = client_data['game_state']['ship_positions']
    if any(ship_matrix[y_coord, x] != '~' for x in range(x_coord, x_coord + 3)):
        client_socket.sendall(json.dumps({"type": "error_response", "player": f"{client_id}", "message": "Cannot place ship here."}).encode())
        return

    # add ship to client's list of ship positions
    ships.append((y_coord, x_coord, 3))  # Store starting position and length

    # add ship to client's ship matrix
    ship_matrix[y_coord, x_coord] = '<'
    ship_matrix[y_coord, x_coord + 1] = '='
    ship_matrix[y_coord, x_coord + 2] = '>'

    # output to server where the ship was placed
    print(f"Client {client_address} placed a ship at {ship_position}. Total ships for this player: {len(ships)}")
    
    # send confirmation back to the client
    client_socket.sendall(json.dumps({
        "type": "place_response",
        "player": f"{client_id}",
        "message": f"Ship placed starting at {ship_position}.",
        "boards": convert_boards(client_data['game_state'])
    }).encode())

def handle_target(client_socket, client_address, message, client_id):
    # ensure client has joined the game (sanity check lol)
    client_data = clients.get(client_address)
    if not client_data:
        client_socket.sendall(json.dumps({"type": "error_response", "player": f"{client_id}", "message": "You must join first."}).encode())
        return
    
    # ensure 2 clients are present before targeting
    if len(clients) < 2:
        client_socket.sendall(json.dumps({"type": "error_response", "player": f"{client_id}", "message": "Wait for another player to join."}).encode())
        return 

    # get the other client's data
    other_client_data = [c for c in clients.values() if c != client_data][0]  # Get opponent's data
    others_ships_matrix = other_client_data['game_state']['ship_positions']

    # ensure targeted space has not been targeted prior
    target = message.get("target").upper()
    targets = client_data['game_state']['targets']
    if target in targets:
        client_socket.sendall(json.dumps({"type": "error_response", "player": f"{client_id}", "message": "You have already targeted this location."}).encode())
        return

    # parse target coordinates
    x_coord = int(target[1:]) - 1  # numerical axis
    y_coord = ord(target[0].upper()) - ord('A')  # alphabetical axis converted from A-J to 1-10 for indexing

    # check if the target is a hit
    if others_ships_matrix[y_coord, x_coord] in {'<', '=', '>'}:
        client_data['game_state']['target_positions'][y_coord, x_coord] = '*'
        others_ships_matrix[y_coord, x_coord] = '*'
        result_message = f"{client_id} hit a ship at {target}!"
    else:
        client_data['game_state']['target_positions'][y_coord, x_coord] = 'o'
        result_message = f"{client_id} missed at {target}."

    # update list of targets this client has targeted
    targets.append(target)

    # output to server the cell that was targeted
    print(f"Client {client_address} targeted {target}")
    
    # send confirmation back to the client
    client_socket.sendall(json.dumps({
        "type": "target_response",
        "player": f"{client_id}",
        "boards": convert_boards(client_data['game_state']),
        "message": result_message
    }).encode())

    # send response to the other client as well
    other_client_data['socket'].sendall(json.dumps({
        "type": "target_response",
        "player": f"{client_id}",
        "boards": convert_boards(other_client_data['game_state']),
        "message": result_message
    }).encode())

def convert_boards(state):
    boards = {
        'ship_positions': state['ship_positions'].tolist(),
        'target_positions': state['target_positions'].tolist()
    }
    return boards

def handle_chat(client_address, message, client_id):
    broadcast_message({"type": "chat_response", "player": f"{client_id}", "message": message.get("message")})
    p_message = message.get("message")
    print(f"Client {client_address} sent a chat: {p_message}")

def handle_quit(client_socket, client_address, client_id):
    # remove client from the game
    broadcast_message({"type": "quit_response", "player": f"{client_id}", "message": f"{client_id} left the game. Closing both clients and resetting game state..."})
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

def getClientID():
    if(len(clients) > 0):
        return "Player 2"
    return "Player 1"

def start_server():
    tcp_port = None

    # Parse command-line arguments for the `-p` flag
    args = sys.argv[1:]
    for i in range(len(args)):
        if args[i] == '-p' and i + 1 < len(args):
            try:
                tcp_port = int(args[i + 1])
            except ValueError:
                print("Error: Port must be an integer.")
                sys.exit(1)

    # Check if the port was provided
    if tcp_port is None:
        print("Usage: python server.py -p PORT")
        sys.exit(1)

    server_ip = "0.0.0.0"
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((server_ip, tcp_port))
    server_socket.listen(5)
    
    assigned_port = server_socket.getsockname()[1]
    print(f"Server started on {server_ip}:{assigned_port}")

    try:
        while True:
            # accept new client connections
            client_socket, client_address = server_socket.accept()

            if(len(clients) < 2):
                print(f"Accepted connection from {client_address}")
                client_handler = threading.Thread(target=handle_client, args=(client_socket, client_address))
                client_handler.start()
            else:
                client_socket.sendall(json.dumps({"type": "third_client", "message": "The maximum number of players has been reached. Please wait for current players to leave their session..."}).encode())

    except KeyboardInterrupt:
        print("\nServer is shutting down...")
    finally:
        # Cleanup: close all open client sockets
        for client in clients:
            client.close()
        server_socket.close()

if __name__ == "__main__":
    start_server()
