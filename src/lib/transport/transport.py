from abc import ABC, abstractmethod
import socket
from typing import Tuple

Address = Tuple[str, int]


class ReliableTransportProtocol(ABC):
    def __init__(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    @abstractmethod
    def send_to(self, data: bytes, address: Address):
        pass

    @abstractmethod
    def recv_from(self) -> Tuple[bytes, Address]:
        pass


class ReliableTransportClientProtocol(ReliableTransportProtocol):
    def __init__(self, target):
        super().__init__()
        self.target = target

    def send(self, data: bytes):
        self.send_to(data, self.target)

    def recv(self) -> bytes:
        return self.recv_from()[0]

    def set_target(self, target):
        self.target = target


class ReliableTransportServerProtocol(ReliableTransportProtocol):
    def __init__(self, source):
        super().__init__()
        self.socket.bind(source)
