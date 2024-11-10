import os
from multiprocessing.connection import Listener, Client
from time import sleep

class NodeServer:
    def __init__(self, node_id, address, all_nodes):
        self.node_id = node_id
        self.address = address
        self.all_nodes = all_nodes
        self.min_proposal = -1
        self.accepted_proposal = None
        self.accepted_value = None
        self.file_path = f"CISC5597_{self.node_id}.txt"

        if not os.path.exists(self.file_path):
            with open(self.file_path, 'w') as f:
                f.write("Initial content of CISC5597\n")

    def handle_client(self, conn):
        """Handle client request to start the proposal process."""
        data = conn.recv()
        proposer_type, value = data.split()
        
        if proposer_type == 'A' and self.node_id == 1:
            self.start_paxos_process(int(value))
        elif proposer_type == 'B' and self.node_id == 3:
            self.start_paxos_process(int(value))
        
        conn.send(f"Proposal initiated by Node {self.node_id} for Proposer {proposer_type}")
        conn.close()

    def start_paxos_process(self, value):
        """Initiate Paxos process starting with Prepare phase."""
        proposal_number = 1  # Increment this for a unique proposal
        print(f"Node {self.node_id}: Starting Paxos process with proposal number {proposal_number} and value {value}.")
        prepare_responses = self.send_prepare(proposal_number)
        
        prepare_ok_count = sum(1 for response in prepare_responses if response['status'] == "PREPARE_OK")
        
        # Step 4: Check majority and set value if any acceptedValues were returned
        if prepare_ok_count >= 2:
            # Choose the highest accepted value if returned in responses
            highest_accepted = max(
                (response for response in prepare_responses if response['accepted_value'] is not None),
                key=lambda x: x['accepted_proposal'], default=None
            )
            if highest_accepted:
                value = highest_accepted['accepted_value']

            # Proceed to Accept phase
            accept_responses = self.send_accept(proposal_number, value)
            accept_ok_count = sum(1 for response in accept_responses if response == "ACCEPT_OK")
            
            # Step 7: Check if value is chosen or retry if rejected
            if accept_ok_count >= 2:
                print(f"Node {self.node_id}: Proposal {proposal_number} with value {value} accepted by majority.")
                self.finalize_value(value)
            else:
                print(f"Node {self.node_id}: Proposal {proposal_number} was rejected. Retrying with a new proposal.")
                # Retry with a new proposal number if rejected
                self.start_paxos_process(value)
        else:
            print(f"Node {self.node_id}: Proposal {proposal_number} was rejected during the Prepare phase.")

    def send_prepare(self, proposal_number):
        """Send Prepare(n) message to all nodes (including self) and collect responses."""
        responses = []
        for node in self.all_nodes:
            address = node[0]
            port = node[1] + 1000  # Assuming port offset for this example
            with Client((address, port)) as conn:
                message = f"PREPARE {proposal_number}"
                conn.send(message)
                response = conn.recv()
                status, accepted_proposal, accepted_value = response.split()
                responses.append({
                    'status': status,
                    'accepted_proposal': int(accepted_proposal) if accepted_proposal != 'None' else None,
                    'accepted_value': int(accepted_value) if accepted_value != 'None' else None
                })
                print(f"Node {self.node_id} received response: {response}")
        return responses

    def send_accept(self, proposal_number, value):
        """Send Accept(n, value) message to all nodes and collect responses."""
        responses = []
        for node in self.all_nodes:
            address = node[0]
            port = node[1] + 1000  # Assuming port offset for this example
            with Client((address, port)) as conn:
                message = f"ACCEPT {proposal_number} {value}"
                conn.send(message)
                response = conn.recv()
                responses.append(response)
                print(f"Node {self.node_id} sent ACCEPT message to {node}, received response: {response}")
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
            print(f"Node {self.node_id}: Accepted ACCEPT proposal {proposal_number} with value {value}.")
            return "ACCEPT_OK"
        else:
            print(f"Node {self.node_id}: Rejected ACCEPT proposal {proposal_number} with value {value}.")
            return "REJECTED"

    def start(self):
        """Start the server and listen for incoming connections."""
        listener = Listener(self.address)
        print(f"Node {self.node_id} started at {self.address}")

        while True:
            conn = listener.accept()
            message = conn.recv()
            parts = message.split()

            if parts[0] == "START_PAXOS":
                proposer_type = parts[1]
                value = int(parts[2])
                if (proposer_type == 'A' and self.node_id == 1) or (proposer_type == 'B' and self.node_id == 3):
                    self.start_paxos_process(value)
                    response = f"Proposal initiated by Node {self.node_id} for Proposer {proposer_type}"
                else:
                    response = "Invalid Proposer"

            elif parts[0] == "PREPARE":
                proposal_number = int(parts[1])
                response = self.handle_prepare(proposal_number)

            elif parts[0] == "ACCEPT":
                proposal_number, value = int(parts[1]), int(parts[2])
                response = self.handle_accept(proposal_number, value)

            else:
                response = "UNKNOWN_COMMAND"

            conn.send(response)
            conn.close()


if __name__ == "__main__":
    all_nodes = [('localhost', 5001), ('localhost', 5002), ('localhost', 5003)]
    nodes = [NodeServer(1, ('localhost', 5001), all_nodes),
             NodeServer(2, ('localhost', 5002), all_nodes),
             NodeServer(3, ('localhost', 5003), all_nodes)]

    for node in nodes:
        node.start()
