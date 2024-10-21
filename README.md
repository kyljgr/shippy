# Shippy
## A battleship-like game implemented using Python & sockets
### By Alex Brown, Kyle Jager, and Chris Urbano
#### This README is a living document. As we continue to improve and make changes, we will update this to best reflect the status of our project.

**How to Play**
1. Clone this repository.
2. **Start the server:** Run the `server.py` script.
     - Run `python3 server.py` in a terminal or command prompt while in the directory where your Shippy files are located. **(Sprint 1)**
3. **Connect clients:** Run the `client.py` script on two different machines or terminals.
     - Input the IP address of the machine your `server.py` file is running on to connect a client. **(Sprint 1)**
4. **Start playing:** See **Rules**.

**Rules**
* Each player places 5 different 'boats' on their grid using coordinates (5L, 4L, 3L, 3L, 2L).
* Then, each player will take turns "shooting" at their opponent's board, with the goal of hitting a coordinate containing one of their ships.
* A player "shoots" by naming a coordinate they would like to target.
* If that coordinate contains a ship, both players will be notified that it was hit, and it will be marked on both boards.
* To "sink" a ship, all of the coordinates that ship is contained on must be hit (for example: A0, A1, and A2 for a 3L ship).
* The first player to sink all ships controlled by their opponent wins.

**Technologies Used**
* Python
* Sockets

**Message Protocol Specification**

The Shippy game uses a JSON-based protocol for communication between the server and clients. The protocol defines the structure and format of the messages exchanged during gameplay, including actions like joining the game, placing ships, targeting, chatting, and quitting.

### Message Types

#### 1. Join Message

- **Type**: `"join"`
- **Data Fields**: None
- **Expected Response**:
    - **Type**: `"info"`
    - **Data Fields**:
        - `"message"`: A string confirming the player has joined, e.g., `"Player [Client Name] joined the game."`

#### 2. Place Message

- **Type**: `"place"`
- **Data Fields**:
    - `"position"`: A string representing the ship’s placement on the grid, e.g., `"A1"`.
- **Expected Response**:
    - **Type**: `"info"` or `"error"`
    - **Data Fields**:
        - `"message"`: `"Ship placed at A1"`, `"Invalid position"`, or `"Maximum ships placed"`

#### 3. Target Message

- **Type**: `"target"`
- **Data Fields**:
    - `"target"`: A string representing the grid coordinate for targeting a ship, e.g., `"B2"`.
- **Expected Response**:
    - **Type**: `"info"` or `"error"`
    - **Data Fields**:
        - `"message"`: `"Fired on B2"`, `"You have already targeted this location"`, or `"You must place all of your ships first"`

#### 4. Chat Message

- **Type**: `"chat"`
- **Data Fields**:
    - `"message"`: A string containing the chat message, e.g., `"Hello!"`.
- **Expected Response**:
    - **Type**: `"info"`
    - **Data Fields**:
        - `"message"`: A string with the broadcasted chat message, e.g., `"[Client Name]: Hello!"` (broadcasted to all clients)

#### 5. Quit Message

- **Type**: `"quit"`
- **Data Fields**: None
- **Expected Response**:
    - **Type**: `"info"`
    - **Data Fields**:
        - `"message"`: `"Player [Client Name] left the game."`

### Error Handling

If there is an issue with the client's request (e.g., invalid position, target, or unauthorized command), the server responds with an `"error"` message type. The error message will contain a human-readable explanation of the issue.

Example error message:

```json
{
    "type": "error",
    "message": "Invalid target"
}

**Additional Resources**
* [Python 3.12.6 Documentation](https://docs.python.org/3/)
* [Python Socket Programming guide from Real Python](https://realpython.com/python-sockets/)
