import os
from threading import Thread
from lib.connection import ConnectionRFTP
from lib.exceptions import FilenNotExists
from lib.packet import (
    TransportPacket,
    ReadRequestPacket,
    WriteRequestPacket,
    ErrorPacket,
    AckFPacket,
)
from lib.server.request_handler import Handler
from lib.transport.consts import Address
from lib.transport.transport import ReliableTransportClient, ReliableTransportServer
from os import path


class Server:
    def __init__(self, address: Address, root_directory: str):
        self.socket = ReliableTransportServer(address)
        self.request_handler = Handler(root_directory)
        self.address = address

    def accept(self):
        data, address = self.socket.recv_from()
        packet = TransportPacket.decode(data)
        self.request_handler.handle_request(packet, address)
