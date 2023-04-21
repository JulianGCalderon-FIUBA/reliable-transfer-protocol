from queue import Queue
from random import random
import threading
from typing import Tuple, Dict
import socket as skt
from lib.transport.consts import BUFSIZE, Address

from lib.transport.stream import ReliableStream

"""
IMPORTANTE:
- EL bufsize esta hardcodeado en 4096. Se podria hacer que sea configurable, pero
    idealmente los packets deberian poder ser segmentados en caso de que sean
    demasiado grandes.
- Falta la implementación de stop and wait. Si encontramos una solución eficiente
    para limitar el tamaño de la ventana de envio, podemos implementarlo con reducir
    el tamaño de la ventana a 1.
- El proocolo es connectionless, por lo que no hay handshake.
"""


class ReliableTransportProtocol:
    def __init__(self):
        self.socket = skt.socket(skt.AF_INET, skt.SOCK_DGRAM)

        self.recv_queue = Queue()
        self.streams: Dict[Address, ReliableStream] = {}

        self.spawn_reader()

    def recv_from(self) -> Tuple[bytes, Address]:
        return self.recv_queue.get()

    def send_to(self, data: bytes, target: Address):
        self.stream_for_address(target).send(data)

    def spawn_reader(self):
        self.thread_handle = threading.Thread(target=self.reader)
        self.thread_handle.start()

    def reader(self):
        socket = self.socket.dup()
        while True:
            data, address = socket.recvfrom(BUFSIZE)

            # MANUAL PACKET LOSS
            while random() < 0.1:
                data, address = socket.recvfrom(BUFSIZE)
            # MANUAL PACKET LOSS

            self.stream_for_address(address).recv(data)

    def stream_for_address(self, address):
        if self.streams.get(address):
            return self.streams[address]

        self.streams[address] = ReliableStream(self.socket, address, self.recv_queue)

        return self.stream_for_address(address)


class ReliableTransportClient(ReliableTransportProtocol):
    def __init__(self, target: Address):
        super().__init__()
        self.target = target

    def send(self, data: bytes):
        self.send_to(data, self.target)

    def recv(self) -> bytes:
        data, source = self.recv_from()
        if source == self.target:
            return data

        return self.recv()


class ReliableTransportServer(ReliableTransportProtocol):
    def __init__(self, address: Address):
        super().__init__()
        self.socket.bind(address)
