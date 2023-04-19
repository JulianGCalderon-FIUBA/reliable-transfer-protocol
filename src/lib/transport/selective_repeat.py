from queue import Queue
from random import random
import threading
import socket
from typing import Tuple, Dict, List

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


class SelectiveRepeatProtocol(ReliableTransportProtocol):
    id = 0
    queue = Queue()
    received: Dict[Address, List[int]] = {}
    timers: Dict[Address, Dict[int, threading.Timer]] = {}
    buffered: Dict[Address, List[(DataPacket)]] = {}
    expected_id: Dict[Address, int] = {}

    def __init__(self):
        super().__init__()

        self.start_read_thread()

    def start_read_thread(self):
        self.read_thread = threading.Thread(target=self.read_thread)
        self.read_thread.start()

    def send_to(self, data: bytes, target: Address):
        data_packet = DataPacket(self.id, data)

        self.send_data_packet(data_packet, target)

        self.id = self.increase_sequence(self.id)

    def send_data_packet(self, packet: DataPacket, target: Address):
        self.start_timer(packet, target)

        self.socket.sendto(packet.encode(), target)

    def start_timer(self, packet: DataPacket, target: Address):
        timer = threading.Timer(
            TIMER_DURATION, lambda: self.send_data_packet(packet, target)
        )
        timer.start()
        self.get_timers(target)[packet.id] = timer

    def read_thread(self):
        while True:
            data, address = self.socket.recvfrom(BUFSIZE)

            # MANUAL PACKET LOSS
            while random() < 0.1:
                data, address = self.socket.recvfrom(BUFSIZE)
            # MANUAL PACKET LOSS

            packet = Packet.decode(data)
            if isinstance(packet, AckPacket):
                self.on_ack_packet(packet, address)

            elif isinstance(packet, DataPacket):
                self.on_data_packet(packet, address)

    def on_ack_packet(self, packet, address):
        try:
            self.get_timers(address).pop(packet.id).cancel()
        except KeyError:
            pass

    def on_data_packet(self, packet, address):
        self.socket.sendto(AckPacket(packet.id).encode(), address)

        if packet.id in self.get_received(address):
            return

        self.add_received(address, packet.id)

        if self.is_expected_id(address, packet.id):
            self.queue.put((packet.data, address))
            self.increase_expected_id(address)
            self.queue_buffered_packets(address)
        else:
            self.get_buffered(address).append(packet)

    def queue_buffered_packets(self, target: Address):
        for packet in self.get_buffered(target):
            if self.is_expected_id(target, packet.id):
                self.get_buffered(target).remove(packet)
                self.queue.put((packet.data, target))
                self.increase_expected_id(target)
                return self.queue_buffered_packets(target)

    def add_received(self, target: Address, id: int):
        if len(self.get_received(target)) <= id % WINDOW_SIZE:
            self.get_received(target).append(id)
        else:
            self.get_received(target)[id % WINDOW_SIZE] = id

    def get_timers(self, target: Address) -> Dict[int, threading.Timer]:
        return self.timers.setdefault(target, {})

    def get_received(self, target: Address) -> List[int]:
        return self.received.setdefault(target, [])

    def get_buffered(self, target: Address) -> List[DataPacket]:
        return self.buffered.setdefault(target, [])

    def is_expected_id(self, address: Address, id: int) -> bool:
        return self.expected_id.setdefault(address, 0) == id

    def increase_expected_id(self, address: Address):
        self.expected_id[address] = self.increase_sequence(self.expected_id[address])

    def increase_sequence(self, number: int) -> int:
        number += 1
        if number == SEQUENCE_NUMBER_LIMIT:
            number = 0

        return number

    def recv_from(self) -> Tuple[bytes, Address]:
        return self.queue.get()


class SelectiveRepeatClientProtocol(
    ReliableTransportClientProtocol, SelectiveRepeatProtocol
):
    pass


class SelectiveRepeatServerProtocol(
    ReliableTransportServerProtocol, SelectiveRepeatProtocol
):
    pass
