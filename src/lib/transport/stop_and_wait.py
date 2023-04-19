from queue import Queue
from random import random
import threading
from typing import Tuple
from lib.transport.packet import AckPacket, DataPacket, Packet
from lib.transport.transport import (
    Address,
    ReliableTransportClientProtocol,
    ReliableTransportProtocol,
    ReliableTransportServerProtocol,
)

BUFSIZE = 4096
TIMER_DURATION = 0.1
WINDOW_SIZE = 10
SEQUENCE_NUMBER_LIMIT = 32767


class StopAndWaitProtocol(ReliableTransportProtocol):
    id: bool = 0
    expected: bool = 0
    queue = Queue()

    def __init__(self):
        super().__init__()

        self.start_read_thread()

    def start_read_thread(self):
        self.read_thread = threading.Thread(target=self.read_thread)
        self.read_thread.start()

    def read_thread(self):
        while True:
            data, address = self.socket.recvfrom(BUFSIZE)

            # MANUAL PACKET LOSS
            while random() < 0.1:
                data, address = self.socket.recvfrom(BUFSIZE)
            # MANUAL PACKET LOSS

            packet = Packet.decode(data)
            if isinstance(packet, AckPacket):
                self.on_ack_packet(packet)

            elif isinstance(packet, DataPacket):
                self.on_data_packet(packet, address)

    def on_ack_packet(self, packet):
        if packet.id == self.id:
            self.timer.cancel()

    def on_data_packet(self, packet, address):
        self.socket.sendto(AckPacket(packet.id).encode(), address)

        if packet.id == self.expected:
            self.queue.put((packet.data, address))
            self.expected = not self.expected

    def send_to(self, data: bytes, target: Address):
        data_packet = DataPacket(self.id, data)

        self.send_data_packet(data_packet, target)

        self.id = not self.id

    def send_data_packet(self, packet: DataPacket, target: Address):
        self.start_timer(packet, target)

        self.socket.sendto(packet.encode(), target)

        self.timer.start()
        self.timer.join()

    def start_timer(self, data_packet: DataPacket, target: Address):
        self.timer = threading.Timer(
            TIMER_DURATION, lambda: self.send_data_packet(data_packet, target)
        )

    def recv_from(self) -> Tuple[bytes, Address]:
        return self.queue.get()

    pass


class StopAndWaitClientProtocol(ReliableTransportClientProtocol, StopAndWaitProtocol):
    pass


class StopAndWaitServerProtocol(ReliableTransportServerProtocol, StopAndWaitProtocol):
    pass
