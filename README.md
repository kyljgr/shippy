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
* The 5 boats avaliable to be placed are of lengths 2, 3, 3, 4, and 5. See the description of the place command for how to place and orient these ships.
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

### Commands (All case-insensitive)

#### 1. Help

- **Description**: `Lists commands and their usages.`
- **Data Fields**: None
- **Example Commands**:
    - `help`: Prints this command information page to the terminal.

#### 2. Place [ship length] [orientation] [start coordinate]

- **Description**: `Places a ship on a players board in the format "place [ship length] [orientation] [start coordinate]"`
- **Data Fields**: 
    - `"ship length"`: The size of the ship you wish to place. The skiff:`2` One of the two avaliable destroyers:`3` The battleship:`4` The aircraft carrier:`5`.
    - `"orientation"`: The orientation of the ship either vertical or horizontal. `h` or `v`.
    - `"start coordinate"`: The left-most, top-most coordinate on the A-J,1-10 coordinate plane that the ship will occupy: `A1` or `d8` or `j10` for example.
- **Expected Response**:
    - May include: `"Ship placed at A1"`, `"Not enough room for ship"`, `"A ship already exists in this location"`, `"You have already placed the maximum number of size-{ship_size} ships"`, or `"Maximum ships placed"`
- **Example Commands**:
    - `place 2 V A1`: A ship of length 2 oriented vertically which takes up the spaces A1 and B1.
    - `place 4 h b3`: A ship of length 4 oriented horizontally which takes up the spaces B3, B4, B5 and B6.

#### 3. Target [coordinate]

- **Description**: `After both players have connected and placed all 5 of their ships, the first player that joined targets the other players ships using "target [coordinate]". The second player follows suit, and so on.`
- **Data Fields**:
    - `"coordinate"`: A string representing the grid coordinate for targeting a ship, e.g., `"B2"`.
- **Expected Response**:
    - May include:`"{username} hit a ship at {target}!"`, `"{username} missed at {target}."`, `"{username} has sunk a battleship!"`, `"You have already targeted this location"`, `"You must place all of your ships first"`, `"Wait for your opponent to place all of their ships."`, or `"Wait for your opponent to make a move."`
- **Example Command**:
    - `target B2`: Fires at the opponents board at the location B2.

#### 4. Chat [Message]

- **Description**: `Sends a chat message to the other player displaying in both players terminal as [Client Name]: [chat message]. Format is "chat [message]"`
- **Data Fields**:
    - `"message"`: A string containing the chat message, e.g., `"Hello!"`.
- **Expected Response**:
    - May include: `"[Client Name]: Hello!"` (Broadcasted to all clients)
- **Example Command**:
    - `chat skill issue`: Broadcasts "[client name]: skill issue" to both clients.

#### 5. Quit

- **Type**: `Exits players client and disconnects any other connected clients, closing any existing sockets and ressetting the game state to prepare the next pair of clients. Format is "quit"`
- **Data Fields**: None
- **Expected Response**:
     - Includes: `"[Client Name] left the game. Closing both clients and resetting game state...` (Broadcasted to all clients)
- **Example Command**:
    - `quit`: Ends all clients on server (max of 2) and resets the game.


### Error Handling

If there is an issue with the client's request (e.g., invalid position, target, or unauthorized command), the server responds with an `"error"` message type. The error message is then output to the client, and another action is prompted for. 

### Server Logging

All events are logged (but not saved) to the server in simple text format.

### Security/Risk Evaluation

The game has a few security issues we need to fix. First off, it doesn't thoroughly check the inputs, which means someone could mess with the game by doing injection attacks or something similar. There's also no way to verify who's who, so it's easy for someone to pretend to be another player or grab their messages. Since all the messages between the server and players are not encrypted, anyone can listen in or interfere with them. The server can also be easily overwhelmed because it doesn’t limit how much data it gets or how often, making it prone to crash under too many requests. Lastly, we're not checking if the data being sent and received is tampered with. In our next updates, we need to clean up the data we get, secure our communications, confirm users’ identities, and make sure the messages are intact to make the game safer.

