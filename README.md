# Shippy
## A battleship-like game implemented using Python & sockets
### By Alex Brown, Kyle Jager, and Chris Urbano
#### This README is a living document. As we continue to improve and make changes, we will update this to best reflect the status of our project.

**How to Play**
1. Clone this repository.
2. **Start the server:** Run the `server.py` script.
     - Run `python server.py -p PORT` in a terminal or command prompt while in the directory where your Shippy files are located. The argument PORT is the port you wish to start the server on and the same port you will input into the clients when starting them.
3. **Connect clients:** Run the `client.py` script on two different machines or terminals.
     - Input the IP address and port number of the machine your `server.py` file is running on in the format `python client.py -i server_IP/URL -p PORT` to connect a client.
4. **Start playing:** See **Rules**.

**Rules**
* Each player places 5 different 'boats' on their grid using coordinates on a 10 by 10 grid ordered from A-J and 1-10. `A2` or `j10` for example.
* Then, each player will take turns "shooting" at their opponent's board, with the goal of hitting a coordinate containing one of their ships.
* A player "shoots" by naming a coordinate they would like to target.
* If that coordinate contains a ship, both players will be notified that it was hit, and it will be marked on both boards.
* To "sink" a ship, all of the coordinates that ship is contained on must be hit (for example: A0, A1, and A2 for a 3L ship).
* The first player to sink all ships controlled by their opponent wins.
* `NOTE` No win conditions have been set as of yet, and ships are currently only one coordinate space large.

**Technologies Used**
* Python
* Sockets
* Threading

**Message Protocol Specification**

The Shippy game uses a JSON-based protocol for communication between the server and clients. The protocol defines the structure and format of the messages exchanged during gameplay, including actions like joining the game, placing ships, targeting, chatting, and quitting.

### Commands

#### 1. Place [coordinate]

- **Type**: `"place"`
- **Data Fields**:
    - `"position"`: A string representing the ship’s placement on the grid, e.g., `"A1"`.
- **Expected Response**:
    - **Type**: `"place_response"` or `"error_response"`
    - **Data Fields**:
        - `"message"`: `"Ship placed at A1"`, `"Invalid position"`, or `"Maximum ships placed"`

#### 2. Target [coordinate]

- **Type**: `"target"`
- **Data Fields**:
    - `"target"`: A string representing the grid coordinate for targeting a ship, e.g., `"B2"`.
- **Expected Response**:
    - **Type**: `"target_response"` or `"error_response"`
    - **Data Fields**:
        - `"message"`: `"Fired on B2"`, `"You have already targeted this location"`, or `"You must place all of your ships first"`

#### 3. Chat [Message]

- **Type**: `"chat"`
- **Data Fields**:
    - `"message"`: A string containing the chat message, e.g., `"Hello!"`.
- **Expected Response**:
    - **Type**: `"chat_response"`
    - **Data Fields**:
        - `"message"`: A string with the broadcasted chat message, e.g., `"[Client Name]: Hello!"` (broadcasted to all clients)

#### 4. Quit

- **Type**: `"quit"`
- **Data Fields**: None
- **Expected Response**:
    - **Type**: `"quit_response"`
    - **Data Fields**:
        - `"message"`: `"Player [Client Name] left the game."`

### Error Handling

If there is an issue with the client's request (e.g., invalid position, target, or unauthorized command), the server responds with an `"error"` message type. The error message is then output to the client, and another action is prompted for. 

### Server Logging

Server logs will be made avaliable in a seperate document in future iterations of the game.

