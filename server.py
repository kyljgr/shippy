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
    broadcast_message({"type": "quit_response", "player": f"{client_id}", "message": f"{client_id} left the game. Closing both clients and resetting game state..."})
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

    # ensure ship does not already exist in this location
    # Use this when ships is updated to contain coordinate arrays for ships instead of current singular coordinate positions. position_exists = any(ship_position in ship['coordinates'] for ship in ships)
    # if position_exists:
    if ship_position in ships:
        client_socket.sendall(json.dumps({"type": "error_response", "player": f"{client_id}", "message": "A ship is already placed here. Try a different spot."}).encode())
        return

    # add ship to client's list of ship positions
    ships.append(ship_position)

    # add ship to client's ship matrix
    # numerical axis
    x_coord = int(ship_position[1:]) - 1
    # alphabetical axis converted from A-J to 1-10 for indexing
    y_coord = ord(ship_position[0].upper()) - ord('A')
    client_data['game_state']['ship_positions'][y_coord, x_coord] = "S"
    
    # output to server where the ship was placed
    print(f"Client {client_address} placed a ship at {ship_position}. Total ships for this player: {len(ships)}")
    
    # send confirmation back to the client
    client_socket.sendall(json.dumps({"type": "place_response", "player": f"{client_id}", "message": f"Ship placed at {ship_position}."}).encode())

def handle_target(client_socket, client_address, message, client_id):
    # ensure client has joined the game (sanity check lol)
    client_data = clients.get(client_address)
    if not client_data:
        client_socket.sendall(json.dumps({"type": "error_response", "player": f"{client_id}", "message": "You must join first."}).encode())
        return
    
    # ensure 2 clients are present before targeting
    if(len(clients) < 2):
        client_socket.sendall(json.dumps({"type": "error_response", "player": f"{client_id}", "message": "Wait for another player to join."}).encode())
        return 
    
    other_client = client_address
    
    for c in clients.values():
        if c.get('address') != client_address:
            other_client = c.get('address')         
    
    # ensure targeted space has not been targeted prior
    target = message.get("target").upper()
    targets = client_data['game_state']['targets']
    if target in targets:
        client_socket.sendall(json.dumps({"type": "error_response", "player": f"{client_id}", "message": "You have already targeted this location."}).encode())
        return

    # ensure all of this clients ships have been placed first
    ships = client_data['game_state']['ships']
    if len(ships) != MAX_SHIPS:
        client_socket.sendall(json.dumps({"type": "error_response", "player": f"{client_id}", "message": "You must place all of your ships first."}).encode())
        return
    
    # ensure all of the other players ships have been placed as well
    other_client_data = clients.get(other_client)
    others_ships = other_client_data['game_state']['ships']
    if len(others_ships) != MAX_SHIPS:
        client_socket.sendall(json.dumps({"type": "error_response", "player": f"{client_id}", "message": "Wait for your opponent to place all of their ships."}).encode())
        return
    
    # ensure turn taking during targeting
    others_targets = other_client_data['game_state']['targets']
    print(client_id)
    if(client_id == "Player 1"):
        if(len(targets) > len(others_targets)):
            client_socket.sendall(json.dumps({"type": "error_response", "player": f"{client_id}", "message": "Wait for your opponent to make a move."}).encode())
            return
    if(client_id == "Player 2"):
        if(len(targets) == len(others_targets)):
            client_socket.sendall(json.dumps({"type": "error_response", "player": f"{client_id}", "message": "Wait for your opponent to make a move."}).encode())
            return

    # update list of targets this client has targeted
    targets.append(target)

    # update target matrix with newly targeted cell
    x_coord = int(target[1:]) - 1
    # alphabetical axis converted from A-J to 1-10 for indexing
    y_coord = ord(target[0].upper()) - ord('A')
    if target in others_ships:
        client_data['game_state']['target_positions'][y_coord, x_coord] = "*"
        other_client_data['game_state']['ship_positions'][y_coord, x_coord] = "*"
    else:
        client_data['game_state']['target_positions'][y_coord, x_coord] = "o"
        other_client_data['game_state']['ship_positions'][y_coord, x_coord] = "o"

    # output to server the cell that was targeted
    print(f"Client {client_address} targeted {target}")
    
    # send confirmation back to the client
    #TODO: if target was a hit specify. if not specify

    client_socket.sendall(json.dumps({"type": "target_response", "player": f"{client_id}", "boards": convert_boards(client_data['game_state']), "message": f"{client_id} fired on {target}."}).encode())
    other_client_data['socket'].sendall(json.dumps({"type": "target_response", "player": f"{client_id}", "boards": convert_boards(other_client_data['game_state']), "message": f"{client_id} fired on {target}."}).encode())

def convert_boards(state):
    boards = {
        'ship_positions': state['ship_positions'].tolist(),
        'target_positions': state['target_positions'].tolist()
    }
    return boards

def handle_chat(client_address, message, client_id):
    broadcast_message({"type": "chat_response", "player": f"{client_id}", "message": message.get("message")})
    print(f"Client {client_address} sent a chat: {message.get("message")}")

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
