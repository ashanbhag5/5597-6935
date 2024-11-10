import socket
import threading
import os

class NodeServer:
    def __init__(self, node_id, address):
        self.node_id = node_id
        self.address = address
        self.accepted_proposal_number = None
        self.min_accepted_proposal_number = -1
        self.accepted_value = None
        self.file_path = f"CISC5597_{self.node_id}.txt"


        if not os.path.exists(self.file_path):
            with open(self.file_path, 'w') as f:
                f.write("Initial content of CISC5597\n")

    def handle_client(self, conn, addr):
        """Handle an incoming client request (PREPARE or ACCEPT)."""
        data = conn.recv(1024).decode()
        if data.startswith("PREPARE"):
            proposal_number = int(data.split()[1])
            print(f"Node {self.node_id} received PREPARE {proposal_number} from {addr}")
            self.min_accepted_proposal_number = max(proposal_number, self.min_accepted_proposal_number)
            response = self.handle_prepare(proposal_number)
            print(f"Node {self.node_id} sending response to PREPARE {proposal_number}: {response}")
        elif data.startswith("ACCEPT"):
            proposal_number = int(data.split()[1])
            value = data.split()[2]
            print(f"Node {self.node_id} received ACCEPT {proposal_number} with value {value} from {addr}")
            response = self.handle_accept(proposal_number, value)
            print(f"Node {self.node_id} sending response to ACCEPT {proposal_number}: {response}")
        else:
            response = "INVALID"

        conn.send(response.encode())
        conn.close()

    def handle_prepare(self, proposal_number):
        """Process a PREPARE message."""
        if self.accepted_proposal_number is None or proposal_number > self.accepted_proposal_number:
            # Update the accepted proposal number and respond with PREPARE_OK
            self.accepted_proposal_number = proposal_number
            return f"PREPARE_OK {self.accepted_proposal_number} "
        else:
            # Respond with a rejection if the proposal number is too low
            return f"REJECTED IN PREPARE STAGE {self.accepted_proposal_number} "

    def handle_accept(self, proposal_number, value):
        """Process an ACCEPT message."""
        if proposal_number >= self.accepted_proposal_number:
            # Accept the proposal and set the accepted value
            self.accepted_proposal_number = proposal_number
            self.accepted_value = value
            print(f"Node {self.node_id} accepted proposal {proposal_number} with value {value}")
            with open(self.file_path, 'w') as f:
                f.write(f"Accepted value: {value}\n")
            return f"ACCEPT_OK {self.accepted_proposal_number} {self.accepted_value}"
        else:
            # Reject if proposal number is lower than the last accepted
            return f"REJECTED IN ACCEPT STAGE {self.accepted_proposal_number} {self.accepted_value}"

    def start(self):
        """Start the server and listen for incoming connections."""
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind(self.address)
        server.listen()
        print(f"Node {self.node_id} started at {self.address}")

        while True:
            conn, addr = server.accept()
            # Create a new thread to handle the incoming request
            thread = threading.Thread(target=self.handle_client, args=(conn, addr))
            thread.start()  # Start the thread

if __name__ == "__main__":
    # Initialize Node 1, Node 2, and Node 3 servers concurrently
    nodes = [
        NodeServer(1, ('localhost', 5001)),
        NodeServer(2, ('localhost', 5002)),
        NodeServer(3, ('localhost', 5003))
    ]

    # Start each node server in a separate thread
    for node in nodes:
        threading.Thread(target=node.start).start()
