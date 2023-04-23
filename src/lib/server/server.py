import os
from lib.connection import ConnectionRFTP
from lib.packet import (
    TransportPacket,
    ErrorPacket,
    AckFPacket,
)
from lib.server.request_handler import Handler
from lib.transport.consts import Address
from lib.transport.transport import ReliableTransportClient, ReliableTransportServer


class Server:
    def __init__(self, address: Address, root_directory: str):
        self.socket = ReliableTransportServer(address)
        self.request_handler = Handler(root_directory)
        self.address = address

        if not os.path.exists(root_directory):
            os.makedirs(root_directory)

    def accept(self):
        data, address = self.socket.recv_from()
        packet = TransportPacket.decode(data)
        self.request_handler.handle_request(packet, address)


class ErrorWorker:
    def __init__(self, target_address: Address, error: Exception) -> None:
        self.error = ErrorPacket.from_exception(error).encode()
        self.socket = ReliableTransportClient(target_address)
        self.target = target_address

    def run(self):
        self.socket.send(self.error)
        self.socket.close()


class WriteWorker:
    def __init__(self, target_address: Address, path_to_file: str):
        self.dump = open(path_to_file, "w")
        self.socket = ReliableTransportClient(target_address)
        self.connection = ConnectionRFTP(self.socket)
        self.target = target_address

    def run(self):
        try:
            self.socket.send_to(AckFPacket(0).encode(), self.target)
            file = self.connection.recieve_file()
            self.dump.write(file.decode())
            self.dump.close()
        except Exception as exception:
            self.on_worker_exception(self.target, exception)

    def on_worker_exception(self, target_address, exception):
        print("Error occured while fullfilling request:", exception)

        error_packet = ErrorPacket.from_exception(Exception()).encode()
        self.socket.send_to(error_packet, target_address)


class ReadWorker:
    def __init__(self, target_address: Address, path_to_file: str):
        self.file_bytes = open(path_to_file, "r").read(-1).encode()
        self.socket = ReliableTransportClient(target_address)
        self.connection = ConnectionRFTP(self.socket)
        self.target = target_address

    def run(self):
        try:
            self.socket.send(AckFPacket(0).encode())
            self.connection.send_file(self.file_bytes)
        except Exception as exception:
            self.on_worker_exception(self.target, exception)

    def on_worker_exception(self, target_address, exception):
        print("Error occured while fullfilling request:", exception)

        error_packet = ErrorPacket.from_exception(Exception()).encode()
        self.socket.send_to(error_packet, target_address)
