# -*- coding:utf-8 -*-

import socket
import threading
import uuid


# Dictionaries to store current clients and their message history
current_clients = {}  # Holds connected clients and their UUIDs
#Format:    Client UUID: Client Link
history = {}  # Keeps track of message exchanges between clients
#Format:   Client1UIUDClient2UIUD: messages


#Function to handle communication with a connected client
#Run in a separate thread for each client
def link_handler(link, client):
    print('server start to receiving msg from [%s:%s]....' % (client[0], client[1]))
    
    #Generate unique identifier for the connected client
    client_id = uuid.uuid4()

    #Store the client in the 'current_clients' dictionary with their UIUD

    current_clients[str(client_id)] = link  # Store the client and its UUID
    current_uid = str(client_id)
    print(f"New connection from {client}. Assigned UUID: {client_id}")
    

    # Send the UUID back to the client
    link.sendall(f'Your assigned UIUD is: {client_id} '.encode())
    
    #Continuously receive messages from the client
    while True:
        try:
            #Receive and decode client message
            client_data = link.recv(1024).decode()

            #If client sends "exit", end communication
            if client_data == "exit":
                print('communication end with [%s:%s]...' % (client[0], client[1]))
                link.sendall("Goodbye".encode()) #Send a goodbye
                del current_clients[current_uid] #Remove client from 'current_clients'
                break

            #If client sends "list", return a list of active clients UIUD
            if client_data == "list":
                strr = ""
                for client_id, client_socket in current_clients.items():
                    strr += f"\n UUID: {client_id} \n"

                link.sendall(strr.encode())
                continue
            #Check if the message is correctly formatted as "UIUD: Message"
            if validate_message(client_data) == True:
                
                receiver_address, receiver_message = get_address(client_data)
                
                #Get the receiver's socket based on their UIUD
                receiver_socket = current_clients.get(receiver_address)  # Use .get to avoid KeyError if uid does not exist

                

                #If the receiver exists, send the message to them
                if receiver_socket:  
                    receiver_socket.send(f"Message from {current_uid}: {receiver_message}".encode())
                    document_message(current_uid, receiver_address, receiver_message)
                    
                else:
                    print(f"Error: No socket found for UID {receiver_address}")
                    link.sendall(f"Error: No socket found for UID {receiver_address}".encode())
            #If the client requests message history with another UUID
            if validate_history_message(client_data):
                receiver_id = get_history_id(client_data)
                history_string = request_history_data(current_uid, receiver_id)
                link.sendall(f"\n\nYour history is:\n{history_string}".encode())
            
                

            else:
                
                print('client from [%s:%s] send a msg：%s' % (client[0], client[1], client_data))
                link.sendall('server had received your msg'.encode())
        except ConnectionResetError:
            print(f"Connection lost with client [{client[0]}:{client[1]}].")
            break
    #Remove client from 'current_clients' after connection is closed
    if current_uid in current_clients:
        del current_clients[current_uid]
        print(f"Client {current_uid} removed. Remaining clients: {list(current_clients.keys())}")

    #Close the connection after communication ends
    link.close()
    
    
    



#Validates if a message is in the format "<UUID>:<Message>"
def validate_message(input_message):
    parts = input_message.split(":", 1)  # Split on the first colon only
    if len(parts) == 2:
        uid, message = parts[0].strip(), parts[1].strip()
        # Add additional checks if necessary, for example:
        if uid and message:  # Ensure both UID and message are non-empty
            return True
    return False


# Splits the message into the recipient's UUID and the actual message
def get_address(data):
    parts = data.split(":", 1)
    return parts[0].strip(), parts[1].strip()  # Ensure both parts are stripped of whitespace



#Function to document messages exchanged between clients
def document_message(sender_address, receiver_address, msg):
    

    #Generate unique message history id on ASCII
    if str(sender_address) > str(receiver_address):
        unique_id = str(sender_address) + str(receiver_address)
    else:
        unique_id = str(receiver_address) + str(sender_address)
    
    #Append the message to the conversation history
    if unique_id in history:
        history[unique_id] += f"\n{sender_address}: {msg}"
    else:
        history[unique_id] = f"{sender_address}: {msg}"
    

#Check if the client is requesting message history
def validate_history_message(message):
    if message.startswith("history "):
        
        # Extract the UUID from the message and check if it's a valid client
        id_str = message.split(" ", 1)[1]
        if id_str not in list(current_clients.keys()):
            return False
        else:
            return True

    else:
        return False

#Extracts UUID from history request message
def get_history_id(message):
    id_str = message.split(" ", 1)[1]
    return id_str

#Retrieves message history between two clients
def request_history_data(sender_id, receiver_id):
    
    #Generate unique history ID in int
    if str(sender_id) > str(receiver_id):
        unique_id = str(sender_id) + str(receiver_id)
    else:
        unique_id = str(receiver_id) + str(sender_id)
    # Return the history if it exists, otherwise indicate that no history is available
    if unique_id not in list(history.keys()):
        return "Not in the list"
    else:
        return history[unique_id]
        





ip_port = ('127.0.0.1', 9999)
sk = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # socket.SOCK_STREAM is tcp
sk.bind(ip_port)
sk.listen(5)

#Is the first thing sent after the bind 
print('start socket server，waiting client...')


#Once connected to client, it asks to create a new thread waiting for messages from the client 
while True:
    conn, address = sk.accept()
    
    print('create a new thread to receive msg from [%s:%s]' % (address[0], address[1]))
    t = threading.Thread(target=link_handler, args=(conn, address))
    t.start()
''