import socket
import pickle
import time
import random

class ProposerClient:
    def __init__(self, proposer_id, node_addresses):
        self.proposer_id = proposer_id
        self.node_addresses = node_addresses
        self.proposal_id = random.randint(1, 1000)
        self.value = f"Value from Proposer {self.proposer_id}"

    def send_prepare(self):
        """Send prepare message to all nodes."""
        responses = []
        for address in self.node_addresses:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect(address)
                prepare_msg = {'type': 'prepare', 'proposal_id': self.proposal_id}
                s.send(pickle.dumps(prepare_msg))
                response = pickle.loads(s.recv(1024))
                responses.append(response)
        
        return responses

    def send_propose(self):
        """Send propose message to all nodes to commit the value."""
        for address in self.node_addresses:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect(address)
                propose_msg = {'type': 'propose', 'proposal_id': self.proposal_id, 'value': self.value}
                s.send(pickle.dumps(propose_msg))
                response = pickle.loads(s.recv(1024))
                if not response['success']:
                    print(f"Proposer {self.proposer_id} failed to propose to node {address}.")
                    return False
        print(f"Proposer {self.proposer_id} successfully committed value: {self.value}")
        return True

    def run(self):
        """Simulate the proposer running the Paxos protocol."""
        print(f"Proposer {self.proposer_id} is starting the proposal with ID {self.proposal_id}.")
        responses = self.send_prepare()

        # Check if a majority (2 out of 3) accepted the prepare phase
        accept_count = sum(1 for r in responses if r['success'])
        if accept_count >= 2:
            print(f"Majority accepted prepare. Proposer {self.proposer_id} will proceed to propose.")
            success = self.send_propose()
            return success
        else:
            print(f"Not enough nodes accepted prepare. Proposal failed.")
            return False

# Example usage
if __name__ == '__main__':
    node_addresses = [('localhost', 5000), ('localhost', 5001), ('localhost', 5002)]  # List of other nodes' addresses
    proposer_client = ProposerClient(proposer_id=1, node_addresses=node_addresses)
    proposer_client.run()
