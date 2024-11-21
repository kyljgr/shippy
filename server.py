import socket
import threading
import json
import numpy
import sys

# maintaining clients and connections/states
clients = {}

# setting max amount of ships
MAX_SHIPS = 5

# To be set false when server is forcibly closed as to not leave any hanging threads
run_thread = True

# initial server setup
def handle_client(client_socket, client_address):
    # Give player id to 1st or 2nd player to join
    client_id = getClientID()
    username = ""
    print(f"New connection from {client_address} ({client_id})")
    client_socket.sendall(json.dumps({"player": f"{client_id}", "message": f"Welcome to Shippy!"}).encode())
    
    while run_thread:
        try:
            # receive data from client
            message = client_socket.recv(1024)
            if not message:
                break
            
            message = json.loads(message.decode())
            message_type = message.get("type")

            if message_type == "join":
                handle_join(client_socket, client_address, client_id, username)
            elif message_type == "place":
                handle_place(client_socket, client_address, message, client_id, username)
            elif message_type == "target":
                handle_target(client_socket, client_address, message, client_id, username)
            elif message_type == "chat":
                handle_chat(client_address, message, client_id, username)
            elif message_type == "username":
                username = message.get("username")
                print(f"{client_id} has named themselves: {username}.")
            elif message_type == "quit":
                break
            else:
                client_socket.sendall(b"Invalid message type")

        except (socket.error, socket.timeout) as e:
            print(f"Error with client {client_address}: {e}")
            break

    # disconnect
    handle_quit(client_socket, client_address, client_id, username)
    client_socket.close()
    remove_client(client_address)
    print(f"Closed connection to client {client_address}...")

def handle_join(client_socket, client_address, client_id, username):
    # game state dictionary
    game_state = {
        'ships': [],
        'targets': [],
        'ship_positions': numpy.full((10, 10), '~', dtype=object),
        'target_positions': numpy.full((10, 10), '~', dtype=object)
    }
    # add client to the game
    clients[client_address] = {'socket': client_socket, 'address': client_address, 'game_state': game_state, 'client_id': client_id, 'username': username}
    broadcast_message({"type": "join_response", "player": f"{client_id}", "message": f"{username} ({client_id}) joined the game."})

def handle_place(client_socket, client_address, message, client_id, username):
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
    ship_size, orientation, start_pos = ship_position.split()
    ship_size = int(ship_size)

    # parse coordinates
    x_coord = int(start_pos[1:]) - 1  # numerical axis
    y_coord = ord(start_pos[0].upper()) - ord('A')  # alphabetical axis converted from A-J to 1-10 for indexing

    allowed_ships = {2: 1, 3: 2, 4: 1, 5: 1}
    if not can_place_ship(ship_size, ships, allowed_ships):
        client_socket.sendall(json.dumps({"type": "error_response", "player": f"{client_id}", "message": f"You have already placed the maximum number of size-{ship_size} ships."}).encode())
        return

    if (orientation == 'H' and x_coord + ship_size > 10) or (orientation == 'V' and y_coord + ship_size > 10):  # Ensure there's room for the ship
        client_socket.sendall(json.dumps({"type": "error_response", "player": f"{client_id}", "message": "Not enough room for ship."}).encode())
        return

    # ensure the cells are not already occupied
    ship_matrix = client_data['game_state']['ship_positions']
    if orientation == 'H' and any(ship_matrix[y_coord, x] != '~' for x in range(x_coord, x_coord + ship_size)):
        client_socket.sendall(json.dumps({"type": "error_response", "player": f"{client_id}", "message": "A ship already exists in this location."}).encode())
        return
    if orientation == 'V' and any(ship_matrix[y, x_coord] != '~' for y in range(y_coord, y_coord + ship_size)):
        client_socket.sendall(json.dumps({"type": "error_response", "player": f"{client_id}", "message": "A ship already exists in this location."}).encode())
        return

    # add ship to client's list of ship positions
    ship_coords = []
    for i in range(ship_size):
        if orientation == "H":
            # Increment column, keep row the same
            new_row = y_coord
            new_col = x_coord + i
        elif orientation == "V":
            # Increment row, keep column the same
            new_row = y_coord + i
            new_col = x_coord
        
        # Convert back to "A1" format
        coord = f"{chr(ord('A') + new_row)}{new_col + 1}"  # Convert row to letter, col to 1-based number
        ship_coords.append(coord)

    # Append the ship's coordinates to the list of ships
    ships.append(ship_coords)    

    # add ship to client's ship matrix
    if(orientation == 'V'):
        ship_matrix[y_coord, x_coord] = '△'
        ship_matrix[y_coord + ship_size-1, x_coord] = '▽'
        for i in range(1, ship_size-1):
            ship_matrix[y_coord + i, x_coord] = '▯'
    if(orientation == 'H'):
        ship_matrix[y_coord, x_coord] = '◁'
        ship_matrix[y_coord, x_coord + ship_size-1] = '▷'
        for i in range(1, ship_size-1):
            ship_matrix[y_coord, x_coord + i] = '▭'

    # output to server where the ship was placed
    print(f"{username} placed a ship at {ship_position}. Total ships for this player: {len(ships)}")
    

    # '▭', '▯', '△', '▷', '▽', '◁'
    # send confirmation back to the client
    client_socket.sendall(json.dumps({
        "type": "place_response",
        "player": f"{client_id}",
        "message": f"Ship placed starting at {start_pos}.",
        "boards": convert_boards(client_data['game_state'])
    }).encode())

def can_place_ship(ship_size, ships, allowed_ships):
    current_count = sum(1 for ship in ships if len(ship) == ship_size)
    return current_count < allowed_ships.get(ship_size, 0)

def handle_target(client_socket, client_address, message, client_id, username):
    # ensure client has joined the game (sanity check lol)
    client_data = clients.get(client_address)
    if not client_data:
        client_socket.sendall(json.dumps({"type": "error_response", "player": f"{client_id}", "message": "You must join first."}).encode())
        return
    
    # ensure 2 clients are present before targeting
    if len(clients) < 2:
        client_socket.sendall(json.dumps({"type": "error_response", "player": f"{client_id}", "message": "Wait for another player to join."}).encode())
        return 

    other_client_data = [c for c in clients.values() if c != client_data][0]
    others_ships_matrix = other_client_data['game_state']['ship_positions']

    # ensure targeted space has not been targeted prior
    target = message.get("target").upper()
    targets = client_data['game_state']['targets']
    if target in targets:
        client_socket.sendall(json.dumps({"type": "error_response", "player": f"{client_id}", "message": "You have already targeted this location."}).encode())
        return

    # ensure all ships are placed
    if len(client_data['game_state']['ships']) != MAX_SHIPS:
        client_socket.sendall(json.dumps({"type": "error_response", "player": f"{client_id}", "message": "You must place all of your ships first."}).encode())
        return
    # ensure opponent has placed all ships
    if len(other_client_data['game_state']['ships']) != MAX_SHIPS:
        client_socket.sendall(json.dumps({"type": "error_response", "player": f"{client_id}", "message": "Wait for your opponent to place all of their ships."}).encode())
        return

    # ensure turn-based
    other_targets = other_client_data['game_state']['targets']
    if (client_id == "Player 1" and len(targets) > len(other_targets)) or (client_id == "Player 2" and len(targets) == len(other_targets)):
        client_socket.sendall(json.dumps({"type": "error_response", "player": f"{client_id}", "message": "Wait for your opponent to make a move."}).encode())
        return

    x_coord = int(target[1:]) - 1
    y_coord = ord(target[0].upper()) - ord('A')

    if others_ships_matrix[y_coord, x_coord] in {'▭', '▯', '△', '▷', '▽', '◁'}:
        client_data['game_state']['target_positions'][y_coord, x_coord] = '*'
        others_ships_matrix[y_coord, x_coord] = '*'
        result_message = f"{username} hit a ship at {target}!"
        if(check_sunk_ships(other_client_data['game_state']['ships'], target, targets)):
            result_message += f"\n{username} has sunk a battleship!"
    else:
        client_data['game_state']['target_positions'][y_coord, x_coord] = 'o'
        others_ships_matrix[y_coord, x_coord] = 'o'
        result_message = f"{username} missed at {target}."

    # update list of targets this client has targeted
    targets.append(target)

    # output to server the cell that was targeted
    print(f"Client {username} targeted {target}")

    # Check for win condition
    if numpy.all(~numpy.isin(others_ships_matrix, ['▭', '▯', '△', '▷', '▽', '◁'])):
        result_message = f"{username} hit a ship at {target}! {username} HAS WON!!! Closing both clients and resetting game state..."
        print(f"{username} ({client_id}) Has won.")

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

def check_sunk_ships(ships, current_target, targets):
    for ship in ships:
        # Track which coordinates of the ship have been hit
        hit_coords = [coord for coord in ship if coord in targets]

        # Check if the ship is one hit away from being fully sunk
        if len(hit_coords) == len(ship) - 1:
            # Identify the remaining (un-hit) coordinate of the ship
            remaining_coord = [coord for coord in ship if coord not in hit_coords][0]
            
            # Only consider the ship as sunk if the current target is the remaining coordinate
            if remaining_coord == current_target:
                return True
    
    return False

def convert_boards(state):
    boards = {
        'ship_positions': state['ship_positions'].tolist(),
        'target_positions': state['target_positions'].tolist()
    }
    return boards

def handle_chat(client_address, message, client_id, username):
    broadcast_message({"type": "chat_response", "player": f"{client_id}", "message": f"{username}: " + message.get("message")})
    print(f"{username} sent a chat: {message.get('message')}")

def handle_quit(client_socket, client_address, client_id, username):
    # remove client from the game
    broadcast_message({"type": "quit_response", "player": f"{client_id}", "message": f"{username} ({client_id}) left. Closing both clients and resetting game state..."})
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
    return "Player 2" if len(clients) > 0 else "Player 1"

def start_server():
    global run_thread
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

            if len(clients) < 2:
                print(f"Accepted connection from {client_address}")
                client_handler = threading.Thread(target=handle_client, args=(client_socket, client_address))
                client_handler.start()
            else:
                client_socket.sendall(json.dumps({"type": "third_client", "message": "The maximum number of players has been reached. Please wait for current players to leave their session..."}).encode())

    except KeyboardInterrupt:
        run_thread = False
        print("\nServer is shutting down...")
    finally:
        # clean up
        for client in clients.values():
            try:
                client['socket'].close()
            except Exception as e:
                print(f"Error closing socket for client {client['address']}: {e}")

if __name__ == "__main__":
    start_server()
