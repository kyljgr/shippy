import socket
import json
import threading
import select
import queue
import time
import sys

# Message Queue for storing server responses that need to be printed before asking for input
mq = queue.Queue()
# Thread timing event used for prompting user only after mq has had time to process all of its elements
display_prompt = threading.Event()
# This clients player ID
My_Id = ""
# Boolean to set false when threads need to be ended due to a quit or the other player quitting
run_threads = True
# Thread spawned server listening event loop for processing all data that is received from the server
def handle_server(sock):
    global My_Id
    global player_quantity
    sock.setblocking(False)

    try:
        while run_threads:

            read, _, _, = select.select([sock], [], [], 5)
        
            if read:
                # Recieved data should never exceed 1024
                data = sock.recv(4096)
                if not data:
                    mq.put("Server closed the connection.")
                    break

                data = json.loads(data.decode())
                message_type = data.get("type")
                message_content = data.get("message")
                player_id = data.get("player")

                # Handle server response based on message type received
                if message_type == "join_response":
                    response = f"Join response from server: {message_content}"
                    # Should be set once and not changed after initial join
                elif message_type == "place_response":
                    state = data.get("boards")
                    response = f"Place response from server: {message_content}" + "\n" + print_boards(state)
                elif message_type == "target_response":
                    state = data.get("boards")
                    response = f"Target response from server: {message_content}" + "\n" + print_boards(state)
                elif message_type == "chat_response":
                    response = f"{player_id}: {message_content}"
                elif message_type == "quit_response":
                    response = f"KILL Quit response from server: {message_content}"
                    mq.put(response)
                    break
                elif message_type == "error_response":
                    response = f"Server response: {message_content}"
                elif message_type == "third_client":
                    response = f"KILL Server Response: {message_content}"
                    mq.put(response)
                    break
                else:
                    response = f"Server response message type not recognised: {message_type}"

                mq.put(player_id + "|" + response)

    except socket.error as e:
        print("Error while recieving data from server: ", e)

def colored_symbol(symbol):
    RESET = "\033[0m"    # Reset to default color
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    GREY = "\033[90m"

    if symbol in ['▭', '▯', '△', '▷', '▽', '◁']:
        return f"{YELLOW}{symbol}{RESET}"    
    elif symbol == '*':
        return f"{RED}{symbol}{RESET}"   # Red for hits
    elif symbol == '~':
        return f"{CYAN}{symbol}{RESET}"
    elif symbol == 'o':
        return f"{BLUE}{symbol}{RESET}"
    return symbol  # Default color for other symbols


def print_boards(game_state):
    # Labels for columns and rows
    boards = ""
    columns = "  " + " ".join([str(i) for i in range(1, 11)])
    rows = "ABCDEFGHIJ"  # Row labels for A-J

    # Extract the two boards
    ship_positions = game_state['ship_positions']
    target_positions = game_state['target_positions']

    # Create horizontal separator lines for the board edges
    top_border = "┌" + "─" * 21 + "┐"
    bottom_border = "└" + "─" * 21 + "┘"

    # Start printing the boards side by side
    boards += " " * 9 + "Your Ships" + " " * 19 + "Your Targets" + "\n"
    boards += "   " + columns + "       " + columns + "\n"
    boards += "   " + top_border + "      " + top_border + "\n"

    # Iterate over each row and print ships and targets side by side
    for i in range(10):
        row_label = rows[i]  # Get row label (A-J)

        # Prepare ship and target row as strings
        ship_row = " ".join(colored_symbol(symbol) for symbol in ship_positions[i])
        target_row = " ".join(colored_symbol(symbol) for symbol in target_positions[i])

        # Print the row with borders, row label, and ship/target contents
        boards += f" {row_label} │ {ship_row} │    {row_label} │ {target_row} │" + "\n"

    # Print bottom borders for both boards
    boards += "   " + bottom_border + "      " + bottom_border + "\n"
    return boards


def print_with_prompt(message, from_me):
    sys.stdout.write('\r' + ' ' * 80 + '\r')  # Clear line
    print(message)
    if not from_me:
        sys.stdout.write("Enter a command: ")
        sys.stdout.flush()


def handle_input():
    while run_threads:
        display_prompt.wait()
        time.sleep(0.1)
        command = input("Enter a command: ")
        mq.put(f"INPUT: {command.strip()}")
        display_prompt.clear()


# TCP communication phase
def tcp_communication(server_ip, tcp_port=12358):
    global run_threads
    try:
        # Create a TCP socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(5)
            s.connect((server_ip, tcp_port))
            print(f"Connected to server {server_ip} on port {tcp_port}")
            data = s.recv(1024)
            data = json.loads(data.decode())
            run_event_loop = True
            if data.get("type") == "third_client":
                run_event_loop = False
                print(data.get("message"))
                return True
            print(data.get("message"))

            My_Id = data.get("player")

            if run_event_loop:
                server_handler = threading.Thread(target=handle_server, args=(s,))
                server_handler.start()

                
                handle_join(s)

                input_handler = threading.Thread(target=handle_input)
                input_handler.start()

            from_me = True

            while run_event_loop:

                # Execute on user input or print server response from mq
                while not mq.empty():
                    message = mq.get()
                
                    if message.startswith("INPUT: "):
                    # Send a message to the server
                        mess = message[len("INPUT: "):]
                        command, sep, content = mess.partition(' ')
                        content = content.strip()

                        if command.lower() == "place":
                            handle_place(s, content.upper())
                        elif command.lower() == "target":
                            handle_target(s, content.upper())
                        elif command.lower() == "chat":
                            handle_chat(s, content)
                        elif command.lower() == "help":
                            handle_help()
                        elif command.lower() == "quit":
                            handle_quit(s)
                            print("Closing connection...")
                        else:
                            print(f"Unrecognized command: {command}")
                    elif message.startswith("KILL"):
                        run_threads = False  # Signal the input_handler thread to stop
                        input_handler.join()
                        server_handler.join()
                        message = message[len("KILL "):]
                        print(message)
                        return True    
                    else:
                        # Print server response
                        sending_player, prnt = message.split('|', 1)

                        if(sending_player == My_Id):
                            from_me = True
                        else:
                            from_me = False
                        
                        print_with_prompt(prnt, from_me)
                        

                    display_prompt.set()

                    
    except (socket.error, socket.timeout) as e:
        print(f"Connection failed for {server_ip}. Error: {e}")
        return False
    
def handle_place(s, place):
    # the ships position
    position = place
    # ensure validity of cell input
    if not is_valid_ship(position):
        print("That position was not recognised. Try the format '3 H A1' (ship size: [2-5], Orientation (horizontal/vertical): [H/V], Leftmost/Topmost coordinate of ship: [A1-J10])")
        return
        
    json_place_message = json.dumps({"type": "place", "position": position})
    s.sendall(json_place_message.encode())
    

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


def handle_chat(s, message):
    # package message into json to send to server
    json_q_message = json.dumps({"type": "chat", "message": message})
    s.sendall(json_q_message.encode())


def handle_help():
    #TODO: help info
    print("help")

def handle_quit(s):
    json_q_message = json.dumps({"type": "quit"})
    s.sendall(json_q_message.encode())


def handle_join(s):
    print("Joining game session...")
    json_j_message = json.dumps({"type": "join"})
    s.sendall(json_j_message.encode())


def is_valid_cell(y_axis, x_axis):
    if(('a' <= y_axis.lower() <= 'j') and (1 <= int(x_axis) <= 10)):
        return True
    return False

def is_valid_ship(input):
    parts = input.split()
    
    # Ensure there are exactly 3 elements (size, orientation, start position)
    if len(parts) != 3:
        return False
    
    # Extract the three components
    ship_size, orientation, start_pos = parts
        
    # Validate size
    size = int(ship_size)
    if not (2 <= size <= 5):  # Adjust size range as per game rules
        return False
        
    # Validate orientation
    if orientation not in ('H', 'V'):
        return False
        
    # Validate start position
    row = start_pos[0]
    if not ('A' <= row <= 'J'):  # Adjust grid row range as per game rules
        return False
    column = start_pos[1:]
    if not (column.isdigit() and 1 <= int(column) <= 10):  # Adjust column range as per game rules
        return False
        
    # All validations passed
    return True

def is_valid_ip(ip_str):
    parts = ip_str.split('.')
    if len(parts) != 4:
        return False
    for part in parts:
        if not part.isdigit() or not (0 <= int(part) <= 255): 
            return False
    return True
  

def main():
    server_ip = None
    server_port = None

    # Parse command-line arguments for flags -i and -p
    args = sys.argv[1:]
    for i in range(len(args)):
        if args[i] == '-i' and i + 1 < len(args):
            server_ip = args[i + 1]
        elif args[i] == '-p' and i + 1 < len(args):
            try:
                server_port = int(args[i + 1])
            except ValueError:
                print("Error: Port must be an integer.")
                return
    # Ensure both -i and -p arguments are provided
    if not server_ip or server_port is None:
        print("Usage: python client.py -i SERVER_IP/DNS -p PORT")
        return
    # Main loop for attempting connection
    while True:
        try:
            # Step 1: Resolve the server IP (URL or IP address)
            resolved_ip = server_ip if is_valid_ip(server_ip) else socket.gethostbyname(server_ip)
            # Step 2: Try to establish TCP communication with the resolved IP
            if tcp_communication(resolved_ip, server_port):
                break
            else:
                print("Failed to communicate with the server. Retry with the format: python client.py -i SERVER_IP/DNS -p PORT")
                break

        except socket.gaierror:
            print("Error: Could not resolve the server URL. Please check the URL/IP and try again.")
            return  # Exit if URL/IP is invalid or cannot be resolved
    

if __name__ == "__main__":
    main()
