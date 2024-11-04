import socket
import json

# TCP communication phase
def tcp_communication(server_ip, tcp_port=12358):
    try:
        # Create a TCP socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(5)
            s.connect((server_ip, tcp_port))
            print(f"Connected to server {server_ip} on port {tcp_port}")
            data = s.recv(1024)
            print(data.decode())

            handle_join(s)

            while True:
                # Send a message to the server
                message = input("Enter a command: ")
                command, sep, content = message.partition(' ')

                if command.lower() == "place":
                    handle_place(s, content)
                elif command.lower() == "target":
                    handle_target(s, content)
                elif command.lower() == "chat":
                    handle_chat(s, content)
                elif command.lower() == "help":
                    handle_help()
                elif command.lower() == "quit":
                    handle_quit(s)
                    print("Closing connection...")
                    return True
                else:
                    print(f"That command {command} was not recognised...")
                    
    except (socket.error, socket.timeout) as e:
        print(f"Connection failed for {server_ip}. Error: {e}")
        return False
    
def handle_place(s, place):
    # the ships position
    position = place
    # ensure validity of cell input
    y_axis = position[0] 
    x_axis = position[1:]
    if not is_valid_cell(y_axis, x_axis):
        print("That position was not recognised. Try the format 'A1'")
        return
        
    json_place_message = json.dumps({"type": "place", "position": position})
    s.sendall(json_place_message.encode())
    
    # get the server response
    data = s.recv(1024)
    data = json.loads(data.decode())
    print("Received response from server: " + data.get("message"))

def handle_target(s, target):
    # the cell to target
    fire = target
    # ensure validity of cell input
    y_axis = fire[0] 
    x_axis = fire[1:]
    if not is_valid_cell(y_axis, x_axis):
        print("That position was not recognised. Try the format 'B2'")
        return

    json_q_message = json.dumps({"type": "target", "target": fire})
    s.sendall(json_q_message.encode())

    data = s.recv(1024)
    data = json.loads(data.decode())
    print("Recieved targeting response from server: " + data.get("message"))

def handle_chat(s, message):
    # package message into json to send to server
    json_q_message = json.dumps({"type": "chat", "message": message})
    s.sendall(json_q_message.encode())

    # recieve and print out response from server
    data = s.recv(1024)
    data = json.loads(data.decode())
    print("Chat: " + data.get("message"))

def handle_help():
    #TODO: help info
    print("help")

def handle_quit(s):
    json_q_message = json.dumps({"type": "quit"})
    s.sendall(json_q_message.encode())
    data = s.recv(1024)
    data = json.loads(data.decode())
    print("Recieved quit response from server: " + data.get("message"))

def handle_join(s):
    print("Joining game session...")
    # Ask the user to enter a username
    username = input("Enter your username (or press Enter for default): ")

    # Send join request with the username to the server
    json_j_message = json.dumps({"type": "join", "username": username})
    try:
        print("Sending join request to the server...")
        s.sendall(json_j_message.encode())
        print("Join request sent successfully.")
    except socket.error as e:
        print(f"Error sending join request: {e}")
        return

    # Receive and process the response from the server
    try:
        print("Waiting for server response...")
        data = s.recv(1024)
        if not data:
            raise ValueError("No response received from server.")
        data = json.loads(data.decode())
        print(data.get("message"))

        # Display the assigned unique ID and username confirmation
        if "player_id" in data:
            print(f"Your unique ID: {data['player_id']}")
            print(f"Your username: {data['username']}")
    except (json.JSONDecodeError, ValueErrort.error) as e:
        print(f"Error receiving response from server: {e}")



def is_valid_cell(y_axis, x_axis):
    if(('a' <= y_axis.lower() <= 'j') and (1 <= int(x_axis) <= 10)):
        return True
    return False

def is_valid_ip(ip_str):
    parts = ip_str.split('.')
    if len(parts) != 4:
        return False
    for part in parts:
        if not part.isdigit() or not (0 <= int(part) <= 255): 
            return False
    return True
  

def main():
    # Step 1: Discover the server's IP
    server_ip = input("Enter the server IP to connect to: ")
    while True:
        if is_valid_ip(server_ip): 
            # Step 2: Connect and start TCP communication with the server
            if tcp_communication(server_ip):
                break
            server_ip = '0'
        else:
            server_ip = input("Could not find the server. Please try again using the format ***.***.***.***: ")
    

if __name__ == "__main__":
    main()
