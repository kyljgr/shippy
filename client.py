import socket

# TCP communication phase
def tcp_communication(server_ip, tcp_port=12358):
    try:
        # Create a TCP socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(5)
            s.connect((server_ip, tcp_port))
            print(f"Connected to server {server_ip} on port {tcp_port}")

            while True:
                # Send a message to the server
                message = input("Enter a message to send (or 'q' to exit): ")
                if message.lower() == 'q':
                    print("Closing connection...")
                    return True

                # Send the message over the TCP connection
                s.sendall(message.encode())

                # Receive the server's response
                data = s.recv(1024)
                print('Received from server:', repr(data))
    except (socket.error, socket.timeout) as e:
        print(f"Connection failed for {server_ip}. Error: {e}")
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
