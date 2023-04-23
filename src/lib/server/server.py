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
from lib.transport.consts import Address
from lib.transport.transport import ReliableTransportClient, ReliableTransportServer
from os import path

class Server:
    def __init__(self, address: Address, root_directory: str):
        self.socket = ReliableTransportServer(address)
        self.root_directory = root_directory
        self.address = address

    def accept(self):
        data, address = self.socket.recv_from()
        packet = TransportPacket.decode(data)
        self.handle_request(packet, address)

    def handle_request(self, packet: 'TransportPacket', address: Address):
        Thread(target=self.check_request, args=[packet, address]).start()

    def check_request(self, request: TransportPacket, address: Address):
        if isinstance(request, ReadRequestPacket):
            return self.check_read_request(request, address)
        elif isinstance(request, WriteRequestPacket):
            return self.check_write_request(request, address)

        print("Received unknown packet type, ignoring...")

    def check_write_request(self, request: WriteRequestPacket, address: Address):
        absolute_path = self.absolute_path(request.name)
        if path.exists(absolute_path):
            ErrorWorker(address, FileExistsError()).run()
            return
        WriteWorker(address, absolute_path).run()

    def check_read_request(self, request: ReadRequestPacket, address: Address):
        absolute_path = self.absolute_path(request.name)

        if not path.exists(absolute_path):
            ErrorWorker(address, FilenNotExists()).run()
            return

        ReadWorker(address, absolute_path).run()

    def absolute_path(self, relative_path: str) -> str:
        return os.path.join(self.root_directory, relative_path)


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
