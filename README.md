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
     - It's helpful to run the command `help` when first starting the game to see these instructions within your client.

**Rules**
* Each player places 5 different 'boats' on their grid using coordinates on a 10 by 10 grid ordered from A-J and 1-10. `A2` or `j10` for example.
* Then, each player will take turns "shooting" at their opponent's board, with the goal of hitting a coordinate containing one of their ships.
* A player "shoots" by naming a coordinate they would like to target.
* If that coordinate contains a ship, both players will be notified that it was hit, and it will be marked on both boards.
* To "sink" a ship, all of the coordinates that ship is contained on must be hit (for example: A0, A1, and A2 for a 3L ship).
* The first player to sink all ships controlled by their opponent wins.

**Technologies Used**
* Python
* Sockets
* Threading

**Message Protocol Specification**

The Shippy game uses a JSON-based protocol for communication between the server and clients. The protocol defines the structure and format of the messages exchanged during gameplay, including actions like joining the game, placing ships, targeting, chatting, and quitting.

### Commands

#### 1. Place [coordinate]

- **Description**: `Places a 1x1 ship on a players board in the format "place [coordinate]"`
- **Data Fields**:
    - `"position"`: A string representing the ship’s placement on the grid, e.g., `"A1"`.
- **Expected Response**:
    - **Type**: `"place_response"` or `"error_response"`
    - **Data Fields**:
        - `"message"`: `"Ship placed at A1"`, `"Invalid position"`, or `"Maximum ships placed"`
- **Example Command**:
  - `place X [length of ship (2-5)] H/V [orientation] A-J1-10 [starting coordinate]`
  - `place 2 V A1`

#### 2. Target [coordinate]

- **Description**: `After both players have connected and placed all 5 of their ships, the first player that joined targets the other players ships using "target [coordinate]". The second player follows suit, and so on.`
- **Data Fields**:
    - `"target"`: A string representing the grid coordinate for targeting a ship, e.g., `"B2"`.
    - `target B2`
- **Expected Response**:
    - **Type**: `"target_response"` or `"error_response"`
    - **Data Fields**:
        - `"message"`: `"Fired on B2"`, `"You have already targeted this location"`, `"You must place all of your ships first"`, `"Wait for your opponent to place all of their ships."`, or `"Wait for your opponent to make a move."`

#### 3. Chat [Message]

- **Description**: `Sends a chat message to the other player displaying in both players terminal as [Client Name]: [chat message]. Format is "chat [message]"`
- **Data Fields**:
    - `"message"`: A string containing the chat message, e.g., `"Hello!"`.
- **Expected Response**:
    - **Type**: `"chat_response"`
    - **Data Fields**:
        - `"message"`: `"[Client Name]: Hello!"` (Broadcasted to all clients)

#### 4. Quit

- **Type**: `Exits players client and disconnects any other connected clients, closing any existing sockets and ressetting the game state to prepare the next pair of clients. Format is "quit"`
- **Data Fields**: None
- **Expected Response**:
    - **Type**: `"quit_response"`
    - **Data Fields**:
        - `"message"`: `"[Client Name] left the game. Closing both clients and resetting game state...` (Broadcasted to all clients)

### Error Handling

If there is an issue with the client's request (e.g., invalid position, target, or unauthorized command), the server responds with an `"error"` message type. The error message is then output to the client, and another action is prompted for. 

### Server Logging

All events are logged (but not saved) to the server in simple text format.

