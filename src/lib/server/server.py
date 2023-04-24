import os
from lib.packet import (
    Packet,
)
from lib.server.request_handler import Handler
from lib.transport.consts import Address
from lib.transport.transport import ReliableTransportServer


class Server:
    """
    Server interface for the RFTP protocol.

    This class is responsible for accepting connections from clients and
    handling their requests."""

    def __init__(self, address: Address, root_directory: str):
        self.socket = ReliableTransportServer(address)
        self.request_handler = Handler(root_directory)
        self.address = address

        if not os.path.exists(root_directory):
            os.makedirs(root_directory)

    def accept(self):
        """
        Accepts a connection from a client and handles its requests."""

        data, address = self.socket.recv_from()

        packet = Packet.decode(data)
        self.request_handler.handle_request(packet, address)
