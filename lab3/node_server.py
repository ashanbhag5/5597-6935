#Atharva Shanbhag & Irakli Kalmikov 
# 11/10/2024 
# Distributed Systems Lab2
import socket
import threading
import os
import random

class NodeServer:
    def __init__(self, node_id, address, all_nodes):
        self.node_id = node_id
        self.address = address
        self.all_nodes = all_nodes
        self.min_proposal = -1
        self.accepted_proposal = None
        self.accepted_value = None
        self.file_path = f"CISC5597_{self.node_id}.txt"
        self.last_proposal_number = 0

        if not os.path.exists(self.file_path):
            with open(self.file_path, 'w') as f:
                f.write("Initial content of CISC5597\n")

    def handle_client(self, conn, addr):
        """Handle client request to start the proposal process."""
        data = conn.recv(1024).decode()
        proposer_type, value = data.split()
        
        if proposer_type == 'A' and self.node_id == 1:
            self.start_paxos_process(int(value))
        elif proposer_type == 'B' and self.node_id == 3:
            self.start_paxos_process(int(value))
        
        conn.send(f"Proposal initiated by Node {self.node_id} for Proposer {proposer_type}".encode())
        conn.close()

    def start_paxos_process(self, value, prop_num):
        self.last_proposal_number += 10
        
        proposal_number = prop_num  # Increment this for a unique proposal
        print(f"Node {self.node_id}: Starting Paxos process with proposal number {proposal_number} and value {value}.")
        
        prepare_responses = self.send_prepare(proposal_number)
        
        # Track number of PREPARE_OK responses
        prepare_ok_count = sum(1 for response in prepare_responses if response['status'] == "PREPARE_OK")
        
        # Ensure majority is reached before proceeding to the next phase
        if prepare_ok_count >= 2:
            print(f"Node {self.node_id}: Got {prepare_ok_count} PREPARE_OK responses out of {len(prepare_responses)}.")
            
            # Step 4: Choose highest accepted value if any accepted values were returned
            highest_accepted = max(
                (response for response in prepare_responses if response['accepted_value'] is not None),
                key=lambda x: x['accepted_proposal'], default=None
            )
            if highest_accepted:
                value = highest_accepted['accepted_value']

            # Proceed to Accept phase
            accept_responses = self.send_accept(proposal_number, value)
            accept_ok_count = sum(1 for response in accept_responses if response == "ACCEPT_OK")
            
            print(f"Node {self.node_id}: Got {accept_ok_count} ACCEPT_OK responses out of {len(accept_responses)}.")
            
            # Step 7: Check if value is chosen or retry if rejected
            if accept_ok_count >= 2:
                print(f"Node {self.node_id}: Proposal {proposal_number} with value {value} accepted by majority.")
                self.finalize_value(value)
            else:
                print(f"Node {self.node_id}: Proposal {proposal_number} was rejected.")
                # Retry with a new proposal number if rejected
                #self.start_paxos_process(value, proposal_number + 1)
        else:
            print(f"Node {self.node_id}: Proposal {proposal_number} was rejected during the Prepare phase.")

    def send_prepare(self, proposal_number):
        """Send Prepare(n) message to all nodes (including self) and collect responses asynchronously."""
        responses = []
        threads = []

        # Define a callback for handling responses
        def handle_response(node, s):
            response = s.recv(1024).decode()
            status, accepted_proposal, accepted_value = response.split()
            responses.append({
                'node': node,
                'status': status,
                'accepted_proposal': int(accepted_proposal) if accepted_proposal != 'None' else None,
                'accepted_value': int(accepted_value) if accepted_value != 'None' else None
            })
            print(f"Node {self.node_id} sent PREPARE message to {node}, received response: {response}")
            s.close()

        # Send prepare messages to all nodes concurrently
        for node in self.all_nodes:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect(node)
            message = f"PREPARE {proposal_number}"
            s.send(message.encode())
            t = threading.Thread(target=handle_response, args=(node, s))
            threads.append(t)
            t.start()

        # Wait for the threads to finish
        for t in threads:
            t.join()

        return responses

    def send_accept(self, proposal_number, value):
        """Send Accept(n, value) message to all nodes and collect responses asynchronously."""
        responses = []
        threads = []

        # Define a callback for handling responses
        def handle_response(node, s):
            response = s.recv(1024).decode()
            responses.append(response)
            print(f"Node {self.node_id} sent ACCEPT message to {node}, received response: {response}")
            s.close()

        # Send accept messages to all nodes concurrently
        for node in self.all_nodes:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect(node)
            message = f"ACCEPT {proposal_number} {value}"
            s.send(message.encode())
            t = threading.Thread(target=handle_response, args=(node, s))
            threads.append(t)
            t.start()

        # Wait for the threads to finish
        for t in threads:
            t.join()

        return responses

    def finalize_value(self, value):
        """Finalize the value and save it to the node's file."""
        self.accepted_value = value
        with open(self.file_path, 'w') as f:
            f.write(f"Accepted value: {value}\n")
        print(f"Node {self.node_id}: Finalized value {value}.")

    def handle_prepare(self, proposal_number):
        """Process a PREPARE message and respond accordingly."""
        if proposal_number > self.min_proposal:
            self.min_proposal = proposal_number
            print(f"Node {self.node_id}: Accepted PREPARE request with proposal number {proposal_number}.")
            return f"PREPARE_OK {self.accepted_proposal or 'None'} {self.accepted_value or 'None'}"
        else:
            print(f"Node {self.node_id}: Rejected PREPARE request with proposal number {proposal_number}.")
            return "REJECTED None None"

    def handle_accept(self, proposal_number, value):
        """Process an ACCEPT message and respond accordingly."""
        if proposal_number >= self.min_proposal:
            self.accepted_proposal = self.min_proposal = proposal_number
            self.accepted_value = value
            print(f"Node {self.node_id}: Accepted proposal {proposal_number} with value {value}.")
            with open(self.file_path, 'w') as f:
                f.write(f"Accepted value: {value}\n")
            return "ACCEPT_OK"
        else:
            print(f"Node {self.node_id}: Rejected ACCEPT proposal {proposal_number} with value {value}.")
            return "REJECTED"

    def start(self):
        """Start the server and listen for incoming connections."""
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind(self.address)
        server.listen()
        print(f"Node {self.node_id} started at {self.address}")

        while True:
            conn, addr = server.accept()
            threading.Thread(target=self.handle_request, args=(conn,)).start()

    def handle_request(self, conn):
        """Handle incoming PREPARE, ACCEPT, and START_PAXOS requests from clients."""
        message = conn.recv(1024).decode()
        parts = message.split()
        
        print(f"Node {self.node_id}: Received message: {message}")

        if parts[0] == "START_PAXOS":
            # Initiate Paxos based on proposer type and value
            proposer_type = parts[1]
            value = int(parts[2])
            if proposer_type == 'A':
                proposal_num = 1
            else:
                proposal_num = 2
            # Only allow Node 1 to initiate for Proposer A and Node 3 for Proposer B
            if (proposer_type == 'A' and self.node_id == 1) or (proposer_type == 'B' and self.node_id == 3):
                print(f"Node {self.node_id}: Initiating Paxos for Proposer {proposer_type} with value {value}.")
                self.start_paxos_process(value, proposal_num)
                response = f"Proposal initiated by Node {self.node_id} for Proposer {proposer_type}"
            else:
                response = "Invalid Proposer"

        elif parts[0] == "PREPARE":
            proposal_number = int(parts[1])
            response = self.handle_prepare(proposal_number)
        elif parts[0] == "ACCEPT":
            proposal_number = int(parts[1])
            value = int(parts[2])
            response = self.handle_accept(proposal_number, value)

        conn.send(response.encode())
        conn.close()

# Initialize nodes and their addresses
nodes = {
    1: ('localhost', 5001),
    2: ('localhost', 5002),
    3: ('localhost', 5003)
}

# Create NodeServer instances for each node
node_servers = [NodeServer(node_id, address, list(nodes.values())) for node_id, address in nodes.items()]

# Start servers for each node in separate threads
for node_server in node_servers:
    threading.Thread(target=node_server.start).start()
