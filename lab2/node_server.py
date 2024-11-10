import socket
import threading
import random
import pickle

class NodeServer:
    def __init__(self, node_id, address, other_addresses):
        self.node_id = node_id
        self.address = address  # (IP, port)
        self.other_addresses = other_addresses  # List of other nodes' addresses
        self.highest_accepted_proposal = None
        self.accepted_value = None
        self.lock = threading.Lock()
        
    def prepare(self, proposal_id):
        """Handle prepare phase of Paxos."""
        with self.lock:
            if self.highest_accepted_proposal is None or proposal_id > self.highest_accepted_proposal:
                self.highest_accepted_proposal = proposal_id
                return True, self.accepted_value
            else:
                return False, self.accepted_value
    
    def propose(self, proposal_id, value):
        """Handle propose phase of Paxos."""
        with self.lock:
            if proposal_id >= self.highest_accepted_proposal:
                self.accepted_value = value
                self.highest_accepted_proposal = proposal_id
                return True
            return False
    
    def handle_request(self, conn, addr):
        """Handle incoming requests from clients (proposers)."""
        data = conn.recv(1024)
        if not data:
            return
        
        message = pickle.loads(data)
        if message['type'] == 'prepare':
            proposal_id = message['proposal_id']
            success, prev_value = self.prepare(proposal_id)
            response = {'type': 'prepare_response', 'success': success, 'prev_value': prev_value}
            conn.send(pickle.dumps(response))
        
        elif message['type'] == 'propose':
            proposal_id = message['proposal_id']
            value = message['value']
            success = self.propose(proposal_id, value)
            response = {'type': 'propose_response', 'success': success}
            conn.send(pickle.dumps(response))

    def start_server(self):
        """Start the node server to listen for incoming proposals."""
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind(self.address)
        server_socket.listen(5)
        print(f"Node {self.node_id} listening on {self.address}")
        
        while True:
            conn, addr = server_socket.accept()
            threading.Thread(target=self.handle_request, args=(conn, addr)).start()

# Example usage
if __name__ == '__main__':
    # Example address format (host, port)
    node_check = int(input("what number: "))
    node_address = ('localhost', node_check)  # This node's address
    other_addresses = [('localhost', 5001), ('localhost', 5002)]  # Other nodes' addresses

    node_server = NodeServer(node_id=1, address=node_address, other_addresses=other_addresses)
    node_server.start_server()
