import socket
import threading
import random
import time

class Node:
    def __init__(self, node_id, address, nodes):
        self.node_id = node_id
        self.address = address
        self.nodes = nodes  # List of all nodes in the system
        self.accepted_value = None
        self.promised_number = None
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind(self.address)
        self.server_socket.listen(5)
        print(f"Node {self.node_id} listening on {self.address}")
    
    def handle_prepare(self, proposed_number):
        """Handle PREPARE request."""
        if self.promised_number is None or proposed_number > self.promised_number:
            self.promised_number = proposed_number
            response = f"PREPARE_OK {self.promised_number} {self.accepted_value if self.accepted_value else 'None'}"
            print(f"Node {self.node_id} responded with: {response}")
            return response
        else:
            response = f"PREPARE_REJECT {self.promised_number}"
            print(f"Node {self.node_id} responded with: {response}")
            return response

    def handle_accept(self, proposed_number, value):
        """Handle ACCEPT request."""
        if proposed_number >= self.promised_number:
            self.promised_number = proposed_number
            self.accepted_value = value
            response = f"ACCEPTED {self.accepted_value}"
            print(f"Node {self.node_id} accepted value {self.accepted_value}")
            return response
        else:
            response = "ACCEPT_REJECTED"
            print(f"Node {self.node_id} rejected the value")
            return response
    
    def listen_for_messages(self):
        """Listen for incoming connections from proposer clients."""
        while True:
            client_socket, _ = self.server_socket.accept()
            message = client_socket.recv(1024).decode()
            print(f"Node {self.node_id} received message: {message}")

            parts = message.split()
            if parts[0] == "PREPARE":
                proposed_number = int(parts[1])
                response = self.handle_prepare(proposed_number)
            elif parts[0] == "ACCEPT":
                proposed_number = int(parts[1])
                value = parts[2]
                response = self.handle_accept(proposed_number, value)

            client_socket.send(response.encode())
            client_socket.close()

    def start(self):
        """Start the server."""
        threading.Thread(target=self.listen_for_messages, daemon=True).start()

if __name__ == "__main__":
    nodes = [
        Node(1, ('localhost', 5001), []),
        Node(2, ('localhost', 5002), []),
        Node(3, ('localhost', 5003), [])
    ]
    
    for node in nodes:
        node.start()

    # Sleep for a while to allow the server to process messages
    time.sleep(60)
