from socket import socket
from threading import Timer
from typing import Dict

from lib.transport.packet import AckPacket, DataPacket, Packet

TIMER: float = 1.0


class SequenceNumber:
    MAX_VALUE: int = 2**16 - 1

    def __init__(self):
        self._value = 0

    def increase(self):
        if self._value == self.MAX_VALUE:
            self._value = 0
        else:
            self._value += 1

    @property
    def value(self) -> int:
        return self._value


class Stream:
    def __init__(self, socket: socket, target, queue):
        self.next_seq = SequenceNumber()
        self.expected = SequenceNumber()
        self.buffer: Dict[int, bytes] = {}
        self.timers: Dict[int, Timer] = {}

        self.socket = socket
        self.target = target
        self.queue = queue

        print(self.queue)

    def send(self, data: bytes):
        packet = DataPacket(self.next_seq._value, data)
        self.send_data_packet(packet)
        self.next_seq.increase()

    def send_data_packet(self, packet: DataPacket):
        self.send_packet(packet)
        self.start_timer_for(packet)

    def start_timer_for(self, packet: DataPacket):
        timer = Timer(TIMER, self.send_data_packet, args=[packet])
        timer.start()
        self.timers[packet.sequence] = timer

    def recv(self, data: bytes):
        packet = Packet.decode(data)
        if isinstance(packet, AckPacket):
            self.handle_ack(packet)
        elif isinstance(packet, DataPacket):
            self.handle_data(packet)

    def handle_ack(self, packet: AckPacket):
        if self.timers.get(packet.sequence):
            self.timers.pop(packet.sequence).cancel()

    def send_packet(self, packet: Packet):
        self.socket.sendto(packet.encode(), self.target)

    def send_ack(self, sequence: int):
        self.send_packet(AckPacket(sequence))

    def handle_data(self, packet: DataPacket):
        if packet.length != len(packet.data):
            return

        self.send_ack(packet.sequence)

        if packet.sequence == self.expected.value:
            self.expected.increase()
            self.queue_packet(packet.data)
            self.queue_buffered()
        elif packet.sequence > self.expected.value:
            self.buffer[packet.sequence] = packet.data

    def queue_packet(self, data: bytes):
        self.queue.put((data, self.target))

    def queue_buffered(self):
        while self.buffer.get(self.expected.value):
            self.queue_packet(self.buffer.pop(self.expected.value))
            self.expected.increase()
