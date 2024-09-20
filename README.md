# shippy
## a battleship-like game implemented using python & sockets
### by Alex Brown, Kyle Jager, and Chris Urbano
#### This README is a living document. As we continue to imrpove and make changes, we will update this to best reflect the status of our project.
**How to Play**
1. Clone this repository.
2. **Start the server:** run the `server.py` script.
3. **Connect clients:** Run the `client.py` script on two different machines or terminals.
4. **Start playing:** See **Rules**.

**Rules**
* Each player places 5 different 'boats' on their grid using coordinates (5L, 4L, 3L, 3L, 2L).
* Then, each player will take turns "shooting" at their opponent's board, with the goal of sinking on of their ships.
* A player "shoots" by naming a coordinate they would like to target.
* If that coordinate contains a ship, both players will be notified that it was hit and it will be marked on both boards.
* To "sink" a ship, all of the coordinates that ship is contained on must be hit (for example: A0, A1, and A2 for a 3L ship)
* The first player to sink all ships controlled by their opponent wins.

**Technologies Used**
* Python
* Sockets

**Additional Resources**
[Python 3.12.6 Documentation](https://docs.python.org/3/)
[Python Socket Programming guide from Real Python](https://realpython.com/python-sockets/)
