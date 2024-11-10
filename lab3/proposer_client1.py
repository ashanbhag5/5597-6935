import asyncio

class ProposerClient:
    def __init__(self, node_address, proposal_value):
        self.node_address = node_address
        self.proposal_value = proposal_value

    async def send_proposal(self):
        """
        Send the proposal to the target node.
        """
        proposal_msg = f"PROPOSE {self.proposal_value}"
        response = await self.send_message(self.node_address, proposal_msg)
        print(f"Proposer received response: {response}")

    async def send_message(self, node_address, message):
        """
        Send a message to a node and get the response.
        """
        reader, writer = await asyncio.open_connection(*node_address)
        writer.write(message.encode())
        await writer.drain()

        data = await reader.read(100)
        response = data.decode()

        print(f"Proposer client sent: {message}")
        writer.close()
        await writer.wait_closed()

        return response

    def start_proposal(self):
        """
        Start the proposer client to send the proposal.
        """
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.send_proposal())


def main():
    # Assuming Node 1 is where the proposer is targeting
    node_address = ('127.0.0.1', 5001)  # Address of Node 1
    proposal_value = 5  # Example proposal value

    proposer_client = ProposerClient(node_address, proposal_value)
    proposer_client.start_proposal()


if __name__ == "__main__":
    main()
