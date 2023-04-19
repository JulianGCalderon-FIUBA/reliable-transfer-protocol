
from queue import Queue
from random import random
import socket
import threading
from typing import Tuple

from lib.transport.packet import AckPacket, DataPacket, Packet
from lib.transport.transport import Address, ReliableTransportClientProtocol, ReliableTransportProtocol, ReliableTransportServerProtocol

BUFSIZE = 4096
TIMER_DURATION = 0.01

class SelectiveRepeatProtocol(ReliableTransportProtocol):
    id = 0
    queue = Queue()
    received = {}
    timers = {}

    def __init__(self, bufsize=BUFSIZE):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.bufsize = bufsize

        self.read_thread = threading.Thread(target=self.start_read)
        self.read_thread.start()

    def send_to(self, data: bytes, target: Address):
        self.sendto_with_id(data, target, self.id)

        self.id += 1

    def sendto_with_id(self, data: bytes, target: Address, id: int):
        packet = DataPacket(id, data)

        timer = threading.Timer(TIMER_DURATION, lambda: self.sendto_with_id(packet.encode(), target, id))
        self.timers.setdefault(target, {})[id] = timer
        timer.start()

        self.socket.sendto(packet.encode(), target)

    
    def start_read(self):
        while True:
            data, address = self.socket.recvfrom(self.bufsize)

            print("PROTOCOL: received packet")

            while random() < 0.5:
                data, address = self.socket.recvfrom(self.bufsize)
                
            packet = Packet.decode(data)
            if isinstance(packet, AckPacket):
                print("PROTOCOL: packet is ack")


                id = packet.id

                self.timers.setdefault(address, {}).pop(id).cancel()

            if isinstance(packet, DataPacket):
                print("PROTOCOL: packet is data")


                id = packet.id

                ack = AckPacket(id)
                self.socket.sendto(ack.encode(), address)

                if id not in self.received.setdefault(address, []):
                    self.received[address].append(id)
                    data = packet.data
                    self.queue.put((data, address))


    def recv_from(self) -> Tuple[bytes, Address]:
        return self.queue.get()

class SelectiveRepeatClientProtocol(ReliableTransportClientProtocol, SelectiveRepeatProtocol):
    pass

class SelectiveRepeatServerProtocol(ReliableTransportServerProtocol, SelectiveRepeatProtocol):
    pass
