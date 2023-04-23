import os
from lib.packet import (
    TransportPacket,
)
from lib.server.request_handler import Handler
from lib.transport.consts import Address
from lib.transport.transport import ReliableTransportServer


class Server:
    def __init__(
            self, address: Address, root_directory: str
            ):
        self.socket = ReliableTransportServer(address)
        self.request_handler = Handler(root_directory)
        self.address = address

        if not os.path.exists(root_directory):
            os.makedirs(root_directory)

    def accept(self):
        data, address = self.socket.recv_from()
        packet = TransportPacket.decode(data)
        self.request_handler.handle_request(packet, address)
