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
                if message.lower() == "place":
                    handle_place(s)
                elif message.lower() == "quit":
                    handle_quit(s)
                    print("Closing connection...")
                    return True
                else:
                    print("That command wasn't recognised...")
                    
    except (socket.error, socket.timeout) as e:
        print(f"Connection failed for {server_ip}. Error: {e}")
        return False
    
def handle_place(s):
    # ask for the ship's position
    position = input("Enter ship position (e.g., A1): ")
    json_place_message = json.dumps({"type": "place", "position": position})
    s.sendall(json_place_message.encode())
    
    # get the server response
    data = s.recv(1024)
    data = json.loads(data.decode())
    print("Received response from server: " + data.get("message"))

def handle_quit(s):
    json_q_message = json.dumps({"type": "quit"})
    s.sendall(json_q_message.encode())
    data = s.recv(1024)
    data = json.loads(data.decode())
    print("Recieved quit response from server: " + data.get("message"))

def handle_join(s):
    print("Joining game session...")
    json_j_message = json.dumps({"type": "join"})
    s.sendall(json_j_message.encode())
    data = s.recv(1024)
    data = json.loads(data.decode())
    print("Recieved join response from server: " + data.get("message"))


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
