# Atharva Shanbhag & Irakli Kalmikov 
# 11/10/2024 
# Distributed Systems Lab2

import socket
import threading
import os

class NodeServer:
    def __init__(self, node_id, address, all_nodes):
        self.node_id = node_id
        self.address = address
        self.all_nodes = all_nodes
        self.min_proposal = 0  # Minimum proposal number this node is willing to accept
        self.accepted_proposal = None  # The last proposal number this node accepted
        self.accepted_value = None  # The last value this node accepted
        self.file_path = f"CISC5597_{self.node_id}.txt"  # Each node maintains a file as part of simulation
        self.last_proposal_number = 0  # Tracks the last proposal number

        # Initialize file if it doesn't exist
        if not os.path.exists(self.file_path):
            with open(self.file_path, 'w') as f:
                f.write("Initial content of CISC5597\n")

    # 1) Proposer: Choose new proposal number n and broadcast Prepare(n) to all servers
    def start_paxos_process(self, value, prop_num):
        proposal_number = self.min_proposal + prop_num
        print(f"Node {self.node_id}: Starting new Paxos protocol as proposer with proposal number {proposal_number} and value {value}")
        prepare_responses = self.send_prepare(proposal_number)

        # 4) Proposer: Count PREPARE_OK responses for majority check
        prepare_ok_count = sum(1 for response in prepare_responses if response['status'] == "PREPARE_OK")
        
        if prepare_ok_count >= 2:
            # If any acceptedValues returned, use highest accepted proposal’s value
            highest_accepted = max(
                (response for response in prepare_responses if response['accepted_value'] is not None),
                key=lambda x: x['accepted_proposal'], default=None
            )
            if highest_accepted:
                value = highest_accepted['accepted_value']
                print(f"Node {self.node_id}: Proposal number {proposal_number} updated with accepted value {value}")

            # Proceed to Accept phase
            accept_responses = self.send_accept(proposal_number, value)
            accept_ok_count = sum(1 for response in accept_responses if response == "ACCEPT_OK")
            
            if accept_ok_count >= 2:
                self.finalize_value(value)

    # Sends a prepare message to all nodes
    def send_prepare(self, proposal_number):
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
            s.close()

        # Broadcast prepare message to all nodes
        for node in self.all_nodes:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect(node)
            message = f"PREPARE {proposal_number}"
            print(f"Node {self.node_id} (Proposer): Sending PREPARE with proposal number {proposal_number} to Node at {node}")
            s.send(message.encode())
            t = threading.Thread(target=handle_response, args=(node, s))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        return responses

    # Sends an accept message to all nodes
    def send_accept(self, proposal_number, value):
        responses = []
        threads = []

        def handle_response(node, s):
            response = s.recv(1024).decode()
            responses.append(response)
            s.close()

        for node in self.all_nodes:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect(node)
            message = f"ACCEPT {proposal_number} {value}"
            print(f"Node {self.node_id} (Proposer): Sending ACCEPT with proposal number {proposal_number} and value {value} to Node at {node}")
            s.send(message.encode())
            t = threading.Thread(target=handle_response, args=(node, s))
            threads.append(t)
            t.start()

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
        if proposal_number > self.min_proposal:
            self.min_proposal = proposal_number
            print(f"Node {self.node_id}: PREPARE_OK for proposal number {proposal_number}.")
            return f"PREPARE_OK {self.accepted_proposal or 'None'} {self.accepted_value or 'None'}"
        else:
            print(f"Node {self.node_id}: PREPARE_REJECTED for proposal number {proposal_number}.")
            return "REJECTED None None"

    def handle_accept(self, proposal_number, value):
        if proposal_number >= self.min_proposal:
            self.accepted_proposal = self.min_proposal = proposal_number
            self.accepted_value = value
            print(f"Node {self.node_id}: ACCEPT_OK for proposal {proposal_number} with value {value}.")
            with open(self.file_path, 'w') as f:
                f.write(f"Accepted value: {value}\n")
            return "ACCEPT_OK"
        else:
            print(f"Node {self.node_id}: REJECTED for ACCEPT proposal {proposal_number} with value {value}.")
            return "REJECTED"

    def start(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind(self.address)
        server.listen()
        print(f"Node {self.node_id} started at {self.address}")

        while True:
            conn, addr = server.accept()
            threading.Thread(target=self.handle_request, args=(conn,)).start()

    def handle_request(self, conn):
        message = conn.recv(1024).decode()
        parts = message.split()

        if parts[0] == "START_PAXOS":
            proposer_type = parts[1]
            value = int(parts[2])
            proposal_num = 5 if proposer_type == 'A' else 7
            if (proposer_type == 'A' and self.node_id == 1) or (proposer_type == 'B' and self.node_id == 3):
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
    1: ('10.128.0.2', 5001),
    2: ('10.128.0.2', 5002),
    3: ('10.128.0.2', 5003)
}

# Create NodeServer instances for each node
node_servers = [NodeServer(node_id, address, list(nodes.values())) for node_id, address in nodes.items()]

# Start servers for each node in separate threads
for node_server in node_servers:
    threading.Thread(target=node_server.start).start()
