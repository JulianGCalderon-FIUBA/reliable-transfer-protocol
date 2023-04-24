from lib.connection import ConnectionRFTP
from lib.logger import normal_log, quiet_log, verbose_log
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
        quiet_log("Error occured while fullfilling request: " + exception.__str__())

        error_packet = ErrorPacket.from_exception(Exception()).encode()
        self.socket.send_to(error_packet, target_address)


class ErrorWorker(Worker):
    def __init__(self, target_address: Address, error: Exception) -> None:
        super().__init__(target_address)

        self.error = ErrorPacket.from_exception(error).encode()
        normal_log(f"Sending {error.__class__.__name__} to {target_address}")

    def run(self):
        self.socket.send(self.error)
        self.socket.close()


class WriteWorker(Worker):
    def __init__(self, target_address: Address, path_to_file: str):
        super().__init__(target_address)
        self.dump = open(path_to_file, "w")
        self.connection = ConnectionRFTP(self.socket)
        self.file_path = path_to_file

    def run(self):
        try:
            self.socket.send_to(AckFPacket().encode(), self.target)
            normal_log(f"Receiving file from: {self.target}")

            file = self.connection.recieve_file()
            verbose_log(f"Writing file into: {self.file_path}")

            self.dump.write(file.decode())
            self.dump.close()
            verbose_log(f"File saved at: {self.file_path}")

        except Exception as exception:
            self.on_worker_exception(self.target, exception)


class ReadWorker(Worker):
    def __init__(self, target_address: Address, path_to_file: str):
        super().__init__(target_address)
        self.file_bytes = open(path_to_file, "r").read(-1).encode()
        self.connection = ConnectionRFTP(self.socket)
        self.file_path = path_to_file

    def run(self):
        try:
            verbose_log(f"Sending file {self.file_path} to {self.target}")
            self.socket.send(AckFPacket().encode())

            self.connection.send_file(self.file_bytes)
            verbose_log(f"File sent to {self.target}")
        except Exception as exception:
            self.on_worker_exception(self.target, exception)
