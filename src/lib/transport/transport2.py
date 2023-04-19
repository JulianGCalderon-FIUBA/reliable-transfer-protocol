from abc import ABC
from enum import Enum
from queue import Queue
from random import random
import socket
from typing import Tuple
import threading

BUFSIZE = 4096
TIMER_DURATION = 0.5

Address = Tuple[str, int]

class TransportProtocol:
    id = 0
    queue = Queue()
    received = {}
    timers = {}

    def __init__(self, bufsize):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.bufsize = bufsize

        self.read_thread = threading.Thread(target=self.start_read)
        self.read_thread.start()

    def sendto(self, data: bytes, target: Address):

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
            while random() < 0.5:
                data, address = self.socket.recvfrom(self.bufsize)
                
            packet = Packet.decode(data)
            if isinstance(packet, AckPacket):
                id = packet.id

                self.timers.setdefault(address, {}).pop(id).cancel()

            if isinstance(packet, DataPacket):
                id = packet.id

                ack = AckPacket(id)
                self.socket.sendto(ack.encode(), address)

                if id not in self.received.setdefault(address, []):
                    self.received[address].append(id)
                    data = packet.data
                    self.queue.put((data, address))


    def receive(self) -> Tuple[bytes, Address]:
        return self.queue.get()




class ClientTransportProtocol(TransportProtocol):
    def __init__(self, target: Address, bufsize=BUFSIZE):
        super().__init__(bufsize)
        self.target = target

    def set_target(self, target: Address):
        self.target = target

    def send(self, data: bytes):
        self.sendto(data, self.target)


class ServerTransportProtocol(TransportProtocol):
    def __init__(self, source: Address, bufsize=BUFSIZE):
        super().__init__(bufsize)
        self.socket.bind(source)

ENDIAN = 'big'

class CODE(Enum):
    ACK = 0
    DATA = 1

class Packet(ABC):
    @classmethod
    def decode(cls, data: bytes):
        opcode = int.from_bytes(data[:2], ENDIAN)
        data = data[2:]

        match opcode:
            case CODE.ACK.value:
                return AckPacket.decode(data)
            case CODE.DATA.value:
                return DataPacket.decode(data)


class AckPacket(Packet):
    def __init__(self, id: int):
        self.opcode = CODE.ACK.value
        self.id = id

    @classmethod
    def decode(cls, stream: bytes):
        id = int.from_bytes(stream[:2], ENDIAN)
        
        return cls(id)
    
    def encode(self) -> bytes:
        return (self.opcode.to_bytes(2, ENDIAN)
                + self.id.to_bytes(2, ENDIAN))


class DataPacket(Packet):
    def __init__(self, id: int, data: bytes):
        self.opcode = CODE.DATA.value
        self.id = id
        self.data = data

    @classmethod
    def decode(cls, stream: bytes):
        id = int.from_bytes(stream[:2], ENDIAN)
        data = stream[2:]
        
        return cls(id, data)


    def encode(self) -> bytes:
        return (self.opcode.to_bytes(2, ENDIAN)
                + self.id.to_bytes(2, ENDIAN)
                + self.data)
