from multiprocessing.connection import Client

class ProposerClient:
    def __init__(self, proposer_type, value, node_address):
        self.proposer_type = proposer_type
        self.value = value
        self.node_address = node_address

    def send_proposal(self):
        try:
            with Client(self.node_address) as conn:
                message = f"START_PAXOS {self.proposer_type} {self.value}"
                conn.send(message)
                response = conn.recv()
                print(f"Response from Node {self.node_address}: {response}")

        except Exception as e:
            print(f"Error while sending proposal to Node {self.node_address}: {e}")

# Usage Example
if __name__ == "__main__":
    node_1_address = ('localhost', 5001)
    node_3_address = ('localhost', 5003)

    proposer_b = ProposerClient(proposer_type='B', value=5, node_address=node_3_address)
    proposer_b.send_proposal()
