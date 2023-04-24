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
    """
    Worker interface for the RFTP protocol.

    This class is responsible for handling requests from clients."""

    def __init__(self, target_address: Address):
        self.socket = ReliableTransportClient(target_address)
        self.target = target_address

    @abstractmethod
    def run(self):
        """
        Runs the worker."""
        pass

    def _on_worker_exception(self, target_address, exception):
        """
        Handles an exception that occured while fulfilling a request,
        and sends an error packet to the client."""

        quiet_log("Error occured while fullfilling request: " + exception.__str__())

        error_packet = ErrorPacket.from_exception(Exception()).encode()
        self.socket.send_to(error_packet, target_address)


class ErrorWorker(Worker):
    """
    Worker for sending error packets to clients."""

    def __init__(self, target_address: Address, error: Exception) -> None:
        super().__init__(target_address)

        self.error = ErrorPacket.from_exception(error).encode()
        verbose_log(f"Sending {error.__class__.__name__} to {target_address}")

    def run(self):
        self.socket.send(self.error)
        self.socket.close()


class WriteWorker(Worker):
    """
    Worker for receiving files from clients."""

    def __init__(self, target_address: Address, path_to_file: str):
        super().__init__(target_address)
        self.connection = ConnectionRFTP(self.socket)
        self.file_path = path_to_file

    def run(self):
        try:
            self.socket.send_to(AckFPacket().encode(), self.target)

            normal_log(f"Recieving file {self.file_path} from {self.target}")
            self.connection.receive_file(self.file_path)
            normal_log(f"File saved at: {self.file_path}")
        except Exception as exception:
            self._on_worker_exception(self.target, exception)


class ReadWorker(Worker):
    """
    Worker for sending files to clients."""

    def __init__(self, target_address: Address, path_to_file: str):
        super().__init__(target_address)
        self.connection = ConnectionRFTP(self.socket)
        self.file_path = path_to_file

    def run(self):
        try:
            self.socket.send(AckFPacket().encode())

            normal_log(f"Sending file {self.file_path} to {self.target}")
            self.connection.send_file(self.file_path)
            normal_log(f"File sent to {self.target}")

        except Exception as exception:
            self._on_worker_exception(self.target, exception)
