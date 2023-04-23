import random
from threading import Thread
from lib.connection import ConnectionRFTP
from lib.exceptions import FailedHandshake, FileExists, FilenNotExists
from lib.packet import (
    Packet,
    ReadRequestPacket,
    WriteRequestPacket,
    ErrorPacket,
    AckFPacket,
)
from lib.transport.consts import Address
from lib.transport.transport import ReliableTransportClient, ReliableTransportServer
from os import path

random.seed(123)


class Server:
    def __init__(self, address: Address, root_directory=".") -> None:
        self.socket = ReliableTransportServer(address)
        self.root_directory = root_directory
        self.address = address

    def listen(self) -> None:
        while True:
            packet, address = self.socket.recv_from()
            handshake = Packet.decode(packet)
            self.handle_client(handshake, address)

    def handle_client(self, handshake: 'Packet', address: Address):
        Thread(target=self.check_request, args=[handshake, address]).start()

    def check_request(self, request: "Packet", address: Address):
        if isinstance(request, ReadRequestPacket):
            return self.check_read_request(request, address)
        elif isinstance(request, WriteRequestPacket):
            return self.check_write_request(request, address)
        print(request)
        raise FailedHandshake()

    def check_write_request(self, request: "WriteRequestPacket", address: Address):
        file_path = self.build_file_path(request.name)
        if path.exists(file_path):
            ErrorWorker(address, FileExists()).run()
            return

        self.attempt_request(address, file_path, write=True)

    def check_read_request(self, request: "ReadRequestPacket", address: Address):
        file_path = self.build_file_path(request.name)
        if not path.exists(file_path):
            ErrorWorker(address, FilenNotExists()).run()
            return

        self.attempt_request(address, file_path, write=False)

    def attempt_request(self, target_address: Address, file_path: str, write):
        try:
            if write:
                WriteWorker(target_address, file_path).run()
            else:
                ReadWorker(target_address, file_path).run()
            return
        except Exception as e:
            print(e)
            ErrorWorker(target_address, Exception()).run()

    def build_file_path(self, filename: str) -> str:
        return self.root_directory + filename


class ErrorWorker:
    def __init__(self, target_address: Address, error: Exception) -> None:
        self.error = ErrorPacket.from_exception(error).encode()
        self.socket = ReliableTransportClient(target_address)
        self.target = target_address

    def run(self):
        self.socket.send(self.error)
        self.socket.close()


class WriteWorker:
    def __init__(self, target_address: Address, path_to_file: str) -> None:
        self.dump = open(path_to_file, "w")
        self.socket = ReliableTransportClient(target_address)
        self.connection = ConnectionRFTP(self.socket)
        self.target = target_address

    def run(self):
        self.socket.send_to(AckFPacket(0).encode(), self.target)
        file = self.connection.recieve_file()
        self.dump.write(file.decode())
        self.dump.close()
        return


class ReadWorker:
    def __init__(self, target_address: Address, path_to_file: str) -> None:
        self.file_bytes = open(path_to_file, "r").read(-1).encode()
        self.socket = ReliableTransportClient(target_address)
        self.connection = ConnectionRFTP(self.socket)
        self.target = target_address

    def run(self):
        self.socket.send(AckFPacket(0).encode())
        self.connection.send(self.file_bytes)
        return  # pending
