import socket
import time
import random

class ProposerClient:
    def __init__(self, node_id, address, all_nodes, value, proposer_type):
        self.node_id = node_id
        self.address = address
        self.all_nodes = all_nodes  # Include all nodes in the system
        self.proposal_number = random.randint(1, 1000)
        self.value = value
        self.proposer_type = proposer_type  # A or B

    def send_prepare(self):
        """Send a PREPARE message to all nodes and return the responses."""
        responses = []
        print(f"Proposer {self.node_id} ({self.proposer_type}) sending PREPARE {self.proposal_number} to all nodes.")
        for node in self.all_nodes:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect(node)
            message = f"PREPARE {self.proposal_number}"
            s.send(message.encode())
            response = s.recv(1024).decode()
            responses.append(response)
            s.close()
        return responses

    def send_accept(self, value):
        """Send an ACCEPT message to all nodes and return the responses."""
        responses = []
        print(f"Proposer {self.node_id} ({self.proposer_type}) sending ACCEPT {self.proposal_number} with value {value}")
        for node in self.all_nodes:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect(node)
            message = f"ACCEPT {self.proposal_number} {value}"
            s.send(message.encode())
            response = s.recv(1024).decode()
            responses.append(response)
            s.close()
        return responses

    def run(self):
        """Run the proposer client to simulate the Paxos process."""
        print(f"Proposer {self.node_id} ({self.proposer_type}) starting with proposal number {self.proposal_number}")

        # Step 1: Send PREPARE messages to all nodes
        prepare_responses = self.send_prepare()

        # Step 2: Wait for majority response to PREPARE
        prepare_ok_responses = [r for r in prepare_responses if r.startswith("PREPARE_OK")]
        if len(prepare_ok_responses) >= 2:
            # Once a majority has responded, proceed with ACCEPT
            # Get the highest accepted value from the responses
            accepted_values = [r.split()[2] for r in prepare_ok_responses if r.split()[2] != 'None']
            if accepted_values:
                # If Proposer A: If there's a value accepted, choose the latest one
                if self.proposer_type == 'A':
                    self.value = accepted_values[0]
                    print(f"Proposer {self.node_id} ({self.proposer_type}) decided on value {self.value} after majority response.")
                # If Proposer B: If no value was accepted, propose a default value
                elif self.proposer_type == 'B':
                    self.value = "B"  # Default value chosen by Proposer B
                    print(f"Proposer {self.node_id} ({self.proposer_type}) decided on default value {self.value} after majority response.")
            else:
                # No value accepted before, Proposer B chooses default value "B"
                if self.proposer_type == 'B':
                    self.value = "B"
                    print(f"Proposer {self.node_id} ({self.proposer_type}) decided on value B since no value was accepted before.")

            # Step 3: Send ACCEPT message with the decided value
            accept_responses = self.send_accept(self.value)
            print(f"Responses to ACCEPT: {accept_responses}")
        else:
            print(f"Proposer {self.node_id} ({self.proposer_type}) did not get a majority response. Proposal rejected.")


if __name__ == "__main__":
    # Define all nodes in the system (Node 1, Node 2, Node 3)
    all_nodes = [('localhost', 5001), ('localhost', 5002), ('localhost', 5003)]

    # Define and run proposer clients (Proposer 1 and Proposer 2)
    # Proposer 1 (Proposal 1 with value A) will run first
    proposer1 = ProposerClient(1, ('localhost', 5001), all_nodes, "A", proposer_type='A')
    proposer1.run()

    #time.sleep(0.0002)  # Shorter delay to simulate Proposer 2 sending right after Proposer 1

    # Proposer 2 (Proposal 2 with value B) runs shortly after Proposer 1
    proposer2 = ProposerClient(2, ('localhost', 5002), all_nodes, 6, proposer_type='B')
    proposer2.run()
