import socket
import time
import random
import threading

class ProposerClient:
    def __init__(self, node_id, address, all_nodes, value, proposal_number, proposer_type):
        self.node_id = node_id
        self.address = address
        self.all_nodes = all_nodes
        self.proposal_number = proposal_number #random.randint(1, 1000)
        self.value = value
        self.proposer_type = proposer_type  # 'A' or 'B'

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
            accepted_values = [r.split()[2] for r in prepare_ok_responses if len(r.split()) > 2 and r.split()[2] != 'None']
            if accepted_values:
                if self.proposer_type == 'A':
                    self.value = accepted_values[0]
                    print(f"Proposer {self.node_id} ({self.proposer_type}) decided on value {self.value} after majority response.")
                elif self.proposer_type == 'B':
                    self.value = accepted_values[0]
                    print(f"Proposer {self.node_id} ({self.proposer_type}) decided on default value {self.value} after majority response.")
            else:
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

    # Function to run each proposer in a separate thread
    def run_proposer(proposer_id, proposer_type, value, proposal_number, delay=0):
        if delay > 0:
            print(f"Proposer {proposer_id} ({proposer_type}) waiting {delay} seconds before starting.")
            time.sleep(delay)
        proposer = ProposerClient(proposer_id, ('localhost', 5001 + proposer_id), all_nodes, value, proposal_number, proposer_type)
        proposer.run()

    # Run both Proposers concurrently using threads
    # Start Proposer A immediately
    thread1 = threading.Thread(target=run_proposer, args=(1, 'A', 3, 700,0))
    # Start Proposer B with a delay of 2 seconds
    thread2 = threading.Thread(target=run_proposer, args=(2, 'B', 5, 800, 2))

    # Start both threads
    thread1.start()
    thread2.start()

    # Wait for both threads to finish
    thread1.join()
    thread2.join()
