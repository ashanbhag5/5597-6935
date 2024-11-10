import random
import time

class Node:
    def __init__(self, node_id, address, other_nodes):
        self.node_id = node_id  # Unique node identifier
        self.address = address  # Node address (IP and port)
        self.other_nodes = other_nodes  # List of other nodes to communicate with
        self.highest_accepted_proposal = None
        self.accepted_value = None
        self.file = "CISC5597"  # Simulated file
    
    def prepare(self, proposal_id):
        """Prepare Phase: A node compares the proposal ID with its highest accepted proposal."""
        if self.highest_accepted_proposal is None or proposal_id > self.highest_accepted_proposal:
            self.highest_accepted_proposal = proposal_id
            return True, self.accepted_value
        else:
            return False, self.accepted_value

    def propose(self, proposal_id, value):
        """Propose Phase: A node accepts a proposal if it has been prepared."""
        if proposal_id >= self.highest_accepted_proposal:
            self.accepted_value = value
            self.highest_accepted_proposal = proposal_id
            return True
        return False
    
    def write_to_file(self, value):
        """Write the chosen value to the file."""
        print(f"Node {self.node_id} writes value '{value}' to {self.file}.")

# Create three nodes (computing nodes in the cluster)
node1 = Node(1, "localhost:5001", [])
node2 = Node(2, "localhost:5002", [])
node3 = Node(3, "localhost:5003", [])
nodes = [node1, node2, node3]

# Connect nodes to each other (fully connected)
node1.other_nodes = [node2, node3]
node2.other_nodes = [node1, node3]
node3.other_nodes = [node1, node2]