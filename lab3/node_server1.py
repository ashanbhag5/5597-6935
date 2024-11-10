import asyncio

class NodeServer:
    def __init__(self, host, port, node_id):
        self.host = host
        self.port = port
        self.node_id = node_id
        self.proposals = {}  # To store proposals
        self.promises = {}  # To store the promises made by acceptors
        self.accepted_values = {}  # To store accepted values

    async def handle_connection(self, reader, writer):
        """
        Handle incoming connections from proposers.
        """
        data = await reader.read(100)
        message = data.decode()
        addr = writer.get_extra_info('peername')
        print(f"Node {self.node_id} received message: {message} from {addr}")

        # Process the message
        if message.startswith("PROPOSE"):
            await self.handle_proposal(message, writer)

        elif message.startswith("PREPARE"):
            await self.handle_prepare(message, writer)

        elif message.startswith("ACCEPT"):
            await self.handle_accept(message, writer)

        writer.close()
        await writer.wait_closed()

    async def handle_proposal(self, message, writer):
        """
        Handle incoming proposal messages and start the Paxos process.
        """
        _, proposal_value = message.split()
        proposal_value = int(proposal_value)

        # Proposer sends a proposal, so we initiate Paxos protocol (Prepare phase)
        await self.broadcast_prepare(proposal_value)

    async def handle_prepare(self, message, writer):
        """
        Handle the PREPARE message from the proposer and send responses.
        """
        _, proposal_number_str = message.split()
        proposal_number = int(proposal_number_str)

        if proposal_number > self.promises.get(self.node_id, -1):  # If proposal number is higher
            self.promises[self.node_id] = proposal_number
            response = f"ACCEPTED {proposal_number}"
            print(f"Node {self.node_id} promises to accept proposal {proposal_number}")
            writer.write(response.encode())
            await writer.drain()

    async def handle_accept(self, message, writer):
        """
        Handle the ACCEPT message and accept the proposal if the conditions are met.
        """
        _, proposal_number_str, value = message.split()
        proposal_number = int(proposal_number_str)

        if proposal_number >= self.promises.get(self.node_id, -1):  # If proposal number is valid
            self.accepted_values[self.node_id] = (proposal_number, value)
            response = f"ACCEPTED {proposal_number} {value}"
            print(f"Node {self.node_id} accepted proposal {proposal_number} with value {value}")
            writer.write(response.encode())
            await writer.drain()

    async def broadcast_prepare(self, proposal_value):
        """
        Broadcast PREPARE messages to other nodes.
        """
        prepare_msg = f"PREPARE {proposal_value}"

        # Here, we will send the PREPARE message to all nodes (including itself)
        # Assuming we know the addresses of the other nodes
        other_nodes = [
            ('127.0.0.1', 5001),  # Node 1 address
            ('127.0.0.1', 5002),  # Node 2 address
            ('127.0.0.1', 5003)   # Node 3 address
        ]

        responses = []
        for node in other_nodes:
            if node != (self.host, self.port):  # Don't send to itself, since it will handle it locally
                response = await self.send_message(node, prepare_msg)
                responses.append(response)

        # Handle responses: when we get a majority (2 out of 3), send ACCEPT
        majority_count = len([response for response in responses if response.startswith("ACCEPTED")])
        if majority_count >= 2:
            await self.broadcast_accept(proposal_value)

    async def broadcast_accept(self, proposal_value):
        """
        Send ACCEPT messages to all nodes once a majority is reached.
        """
        accept_msg = f"ACCEPT {proposal_value} {proposal_value}"

        other_nodes = [
            ('127.0.0.1', 5001),
            ('127.0.0.1', 5002),
            ('127.0.0.1', 5003)
        ]

        for node in other_nodes:
            if node != (self.host, self.port):
                await self.send_message(node, accept_msg)

    async def send_message(self, node_address, message):
        """
        Send a message to another node and return the response.
        """
        reader, writer = await asyncio.open_connection(*node_address)
        writer.write(message.encode())
        await writer.drain()

        data = await reader.read(100)
        response = data.decode()

        print(f"Node {self.node_id} received response: {response}")
        writer.close()
        await writer.wait_closed()

        return response

    async def start_server(self):
        """
        Start the server for the node.
        """
        server = await asyncio.start_server(
            self.handle_connection, self.host, self.port
        )
        addr = server.sockets[0].getsockname()
        print(f"Node {self.node_id} serving on {addr}")
        await server.serve_forever()


def main():
    node_1 = NodeServer('127.0.0.1', 5001, 1)
    node_2 = NodeServer('127.0.0.1', 5002, 2)
    node_3 = NodeServer('127.0.0.1', 5003, 3)

    # Running all nodes concurrently
    loop = asyncio.get_event_loop()
    loop.create_task(node_1.start_server())
    loop.create_task(node_2.start_server())
    loop.create_task(node_3.start_server())
    loop.run_forever()


if __name__ == "__main__":
    main()
