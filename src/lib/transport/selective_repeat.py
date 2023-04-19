
from queue import Queue
from random import random
import threading
import socket
from typing import Tuple, Dict, List

from lib.transport.packet import AckPacket, DataPacket, Packet
from lib.transport.transport import Address, ReliableTransportClientProtocol, ReliableTransportProtocol, ReliableTransportServerProtocol

BUFSIZE = 4096
TIMER_DURATION = 0.1
SOCKET_TIMEOUT = 0.1
WINDOW_SIZE = 10
SEQUENCE_NUMBER_LIMIT = 32767

class SelectiveRepeatProtocol(ReliableTransportProtocol):
    id = 0
    queue = Queue()
    received: Dict[Address, List[int]] = {}
    timers: Dict[Address, Dict[int, threading.Timer]] = {}
    online: bool = True

    def __init__(self):
        super().__init__()

        self.socket.settimeout(SOCKET_TIMEOUT)
        self.read_thread = threading.Thread(target=self.start_read)
        self.read_thread.start()

    def send_to(self, data: bytes, target: Address):
        data_packet = DataPacket(self.id, data)

        self.send_data_packet(data_packet, target)

        self.increase_id_number()

    def send_data_packet(self, packet: DataPacket, target: Address):
        self.start_timer(packet, target)

        self.socket.sendto(packet.encode(), target)

    def start_timer(self, packet: DataPacket, target: Address):
        timer = threading.Timer(TIMER_DURATION, lambda: self.send_data_packet(packet, target))
        timer.start()
        self.get_timers(target)[packet.id] = timer


    def get_timers(self, target: Address) -> Dict[int, threading.Timer]:
        return self.timers.setdefault(target, {})

    def get_received(self, target: Address) -> List[int]:
        return self.received.setdefault(target, [])

    def add_received(self, target: Address, id: int):
        if len(self.get_received(target)) <= id%WINDOW_SIZE:
            self.get_received(target).append(id)
        else:
            self.get_received(target)[id%WINDOW_SIZE] = id

    def increase_id_number(self):
        self.id += 1
        if self.id == SEQUENCE_NUMBER_LIMIT:
            self.id = 0
    
    def start_read(self):
        while self.online:
            try:
                data, address = self.socket.recvfrom(BUFSIZE)
            except socket.error:
                continue

            # MANUAL PACKET LOSS
            while random() < 0.5:
                try:
                    data, address = self.socket.recvfrom(BUFSIZE)
                except socket.error:
                    continue
            # MANUAL PACKET LOSS

            packet = Packet.decode(data)
            if isinstance(packet, AckPacket):
                try:
                    self.get_timers(address).pop(packet.id).cancel()
                except KeyError:
                    pass

            elif isinstance(packet, DataPacket):
                self.socket.sendto(AckPacket(packet.id).encode(), address)

                if packet.id not in self.get_received(address):
                    self.add_received(address, packet.id)
                    self.queue.put((packet.data, address))


    def recv_from(self) -> Tuple[bytes, Address]:
        return self.queue.get()
    
    def terminate(self):
        self.online = False

class SelectiveRepeatClientProtocol(ReliableTransportClientProtocol, SelectiveRepeatProtocol):
    pass

class SelectiveRepeatServerProtocol(ReliableTransportServerProtocol, SelectiveRepeatProtocol):
    pass
