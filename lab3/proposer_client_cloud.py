#Atharva Shanbhag & Irakli Kalmikov 
# 11/10/2024 
# Distributed Systems Lab 2
import socket
import threading
import time

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
    node_1_address = ('10.128.0.2', 5001)
    node_3_address = ('10.128.0.2', 5003)
    
    # One Proposal
    # proposer_a = ProposerClient(proposer_type='A', value=3, node_address=node_1_address)
    # client_a = threading.Thread(target=proposer_a.send_proposal, args=())
    
    # client_a.start()

    # Conflicting Proposals
    # SCENARIO 1 A wins:

    proposer_a = ProposerClient(proposer_type='A', value=3, node_address=node_1_address)
    client_a = threading.Thread(target=proposer_a.send_proposal, args=())
    proposer_b = ProposerClient(proposer_type='B', value=5, node_address=node_3_address)
    client_b = threading.Thread(target=proposer_b.send_proposal, args=())
    
    client_a.start()
    time.sleep(1)
    client_b.start()
    
    #SCENARIO 2 B wins(COMMENT IT OUT):
    # proposer_a = ProposerClient(proposer_type='A', value=8, node_address=node_1_address)
    # client_a = threading.Thread(target=proposer_a.send_proposal, args=())
    # proposer_b = ProposerClient(proposer_type='B', value=10, node_address=node_3_address)
    # client_b = threading.Thread(target=proposer_b.send_proposal, args=())
    
    # client_a.start()
    # time.sleep(0.002)
    # client_b.start()  


