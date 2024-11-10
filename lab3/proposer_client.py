import socket

class ProposerClient:
    def __init__(self, proposer_type, value, node_address):
        """
        Initialize the client with the proposer type, value to propose, and target node address.
        """
        self.proposer_type = proposer_type
        self.value = value
        self.node_address = node_address

    def send_proposal(self):
        """
        Send the proposal initiation command to the designated node server.
        """
        try:
            # Establish a connection to the target node
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect(self.node_address)
                # Send START_PAXOS message with proposer type and value
                message = f"START_PAXOS {self.proposer_type} {self.value}"
                s.send(message.encode())
                
                # Receive response from the server
                response = s.recv(1024).decode()
                print(f"Response from Node {self.node_address}: {response}")
                
        except Exception as e:
            print(f"Error while sending proposal to Node {self.node_address}: {e}")

# Usage Example
if __name__ == "__main__":
    # Define addresses for each node
    node_1_address = ('localhost', 5001)
    node_3_address = ('localhost', 5003)
    
    # Example for Proposer Client A (connects to Node 1)
    #proposer_a = ProposerClient(proposer_type='A', value=3, node_address=node_1_address)
    #proposer_a.send_proposal()

    # Example for Proposer Client B (connects to Node 3)
    proposer_b = ProposerClient(proposer_type='B', value=5, node_address=node_3_address)
    proposer_b.send_proposal()
