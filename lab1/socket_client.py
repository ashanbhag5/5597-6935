# -*- coding:utf-8 -*-

import socket
import threading

# Define the IP address and port number of the server
ip_port = ('127.0.0.1', 9999)
stop_receiving = False
# Function to handle receiving messages from the server
def receive_messages(sock):
    
    while not stop_receiving:
        
            # Receive up to 1024 bytes of data from the server and decode it
            server_reply = sock.recv(1024).decode()
            
            # If a message is received from the server, print it
            print(f"Server Message: {server_reply}")
            if server_reply != "Goodbye":
                
                print("input msg: ", end="", flush=True)
            

            
            
            

        # Catch any errors that occur while receiving messages
        

# Create a socket object for communication
s = socket.socket()

# Connect the socket to the server using the defined IP address and port
s.connect(ip_port)

# Receive the initial message from the server (like a welcome message) and print it
# server_reply = s.recv(1024).decode()
# print(server_reply)

# Start a separate thread to handle receiving messages from the server
receive_thread = threading.Thread(target=receive_messages, args=(s,))
receive_thread.daemon = True  # Set the thread as a daemon, allowing it to exit when the main program ends
receive_thread.start()

# Main loop to handle sending messages to the server
while True:
    # Get input from the user, remove any extra spaces
    # if first:
    #     print("input msg: ", end="")
    #     first=False
         
    inp = input().strip()

    # Skip sending if the input is empty
    if not inp:
        continue

    # Send the user's input as a message to the server
    s.sendall(inp.encode())

    # If the user types 'exit', end the communication and break the loop
    if inp.lower() == "exit":
        
        stop_receiving = True
        receive_thread.join()
        print("Communication ended!")
        
        break
        
        
# Close the socket after the communication has ended
s.close()
