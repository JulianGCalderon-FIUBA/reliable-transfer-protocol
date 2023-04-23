from lib.connection import ConnectionRFTP
from lib.packet import (
    ErrorPacket,
    AckFPacket,
)
from lib.transport.consts import Address
from lib.transport.transport import ReliableTransportClient
from abc import ABC, abstractmethod


class Worker(ABC):

    def __init__(self, target_address: Address):
        self.socket = ReliableTransportClient(target_address)
        self.target = target_address

    @abstractmethod
    def run(self):
        pass

    def on_worker_exception(self, target_address, exception):
        print("Error occured while fullfilling request:", exception)

        error_packet = ErrorPacket.from_exception(Exception()).encode()
        self.socket.send_to(error_packet, target_address)


class ErrorWorker(Worker):
    def __init__(self, target_address: Address, error: Exception) -> None:
        super().__init__(target_address)
        self.error = ErrorPacket.from_exception(error).encode()

    def run(self):
        self.socket.send(self.error)
        self.socket.close()


class WriteWorker(Worker):
    def __init__(self, target_address: Address, path_to_file: str):
        super().__init__(target_address)
        self.dump = open(path_to_file, "w")
        self.connection = ConnectionRFTP(self.socket)

    def run(self):
        try:
            self.socket.send_to(AckFPacket(0).encode(), self.target)
            file = self.connection.recieve_file()
            self.dump.write(file.decode())
            self.dump.close()
        except Exception as exception:
            self.on_worker_exception(self.target, exception)


class ReadWorker(Worker):
    def __init__(self, target_address: Address, path_to_file: str):
        super().__init__(target_address)
        self.file_bytes = open(path_to_file, "r").read(-1).encode()
        self.connection = ConnectionRFTP(self.socket)

    def run(self):
        try:
            self.socket.send(AckFPacket(0).encode())
            self.connection.send_file(self.file_bytes)
        except Exception as exception:
            self.on_worker_exception(self.target, exception)
