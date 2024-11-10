import socket 
import threading
import uuid 
import time
import random 
import sys

node_addresses = [('127.0.0.1', 9998), ('127.0.0.1', 9999), ('127.0.0.1', 10000)]
node_address = (sys.argv[1], int(sys.argv[2]))


highest_promised_id = 0
accepted_value = None
accepted_id = None

file_content = "Initial content of CISC5597"

node_id = None

def paxos_prepare(proposal_id, proposed_value):
    global highest_promised_id, accepted_value, accepted_id

    if highest_promised_id is None or proposal_id > highest_promised_id:
        highest_promised_id = proposal_id
        return ('promise', accepted_id, accepted_value)
    else:
        return ('reject',)
    
def paxos_prepare(proposal_id, value):
    global highest_promised_id, accepted_value, accepted_id

    if proposal_id >= highest_promised_id:
        highest_promised_id = proposal_id
        accepted_id = proposal_id
        accepted_value = value
        return ('accepted', accepted_id, accepted_value)
    else:
        return ('reject',)
    
def handle_incoming_message(conn):
    global file_content

    while True:
        try:
            message = conn.recv(1024).decode()
            if not message:
                break
            parts = message.split('|')
            msg_type = parts[0]

            if msg_type == 'prepare':
                proposal_id = int(parts[1])
                proposed_value = parts[2]
                response = paxos_prepare(proposal_id, proposed_value)
            elif msg_type == 'accept':
                proposal_id = int(parts[1])
                value = parts[2]
                response = paxos_accept(proposal_id, value)
                conn.sendall(f"{response[0]}|{response[1]}|{response[2]}".encode())
            elif msg_type == 'update':
                file_content = parts[1]
                print(f"File updated to: {file_content}")
        except ConnectionResetError:
            break
    conn.close()

def start_server(node_address):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(node_address)
    server_socket.listen(5)
    print(f"Node server started at {node_address}")

    while True:
        conn, _ = server_socket.accept()
        threading.Thread(target=handle_incoming_message, args=(conn,)).start()

def send_prepare_request(node, proposal_id, value):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(node)
        sock.sendall(f"prepare|{proposal_id}|{value}".encode())
        response = sock.recv(1024).decode().split('|')
        return response
    except ConnectionRefusedError:
        return None

def send_accept_request(node, proposal_id, value):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(node)
        sock.sendall(f"accept|{proposal_id}|{value}".encode())
        response = sock.recv(1024).decode().split('|')
        return response
    except ConnectionRefusedError:
        return None

def proposer_propose(value):
    proposal_id = int(time.time() * 1000)  # Use timestamp as unique proposal ID
    promises_received = 0

    for node in node_addresses:
        if node != node_id:
            response = send_prepare_request(node, proposal_id, value)
            if response and response[0] == 'promise':
                promises_received += 1

    if promises_received > len(node_addresses) // 2:  # Majority
        acceptances_received = 0
        for node in node_addresses:
            if node != node_id:
                response = send_accept_request(node, proposal_id, value)
                if response and response[0] == 'accepted':
                    acceptances_received += 1

        if acceptances_received > len(node_addresses) // 2:
            print("Consensus reached! Updating file...")
            for node in node_addresses:
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.connect(node)
                    sock.sendall(f"update|{value}".encode())
                    sock.close()
                except ConnectionRefusedError:
                    continue
    else:
        print("Consensus not reached. Retrying...")

# Start server on each node
def run_node(addresses):
    global node_id
    node_id = address
    threading.Thread(target=start_server, args=(address,)).start()
    time.sleep(2)  # Wait for server to initialize

    while True:
        # Periodically propose a new value to simulate updating the file
        value = f"Updated content at {time.time()}"
        proposer_propose(value)
        time.sleep(random.randint(5, 10))

# Start each node in a separate thread
for address in node_addresses:
    threading.Thread(target=run_node, args=(address,)).start()