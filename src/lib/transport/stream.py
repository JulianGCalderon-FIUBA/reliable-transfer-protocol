from queue import Queue
from socket import socket
from threading import Semaphore, Timer, Lock
from typing import Dict
from lib.transport.consts import DROP_THRESHOLD, TIMER, WINDOW_SIZE, Address

from lib.transport.transport_packet import (
    SEQUENCE_BYTES,
    TransportAckPacket,
    TransportDataPacket,
    InvalidPacketException,
    TransportPacket,
)


class SequenceNumber:

    """
    The sequence numbers are unsigned 16-bit integers, increasing in
    each sent packet. When reaching the maximum value, it is reset to 0."""

    MAX_VALUE: int = SEQUENCE_BYTES**16 - 1

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


class ReliableStream:

    """
    This class implements reliable and ordered data transmission over
    a UDP socket with a specific recipient.

    Since the stream does not actively read from the socket, it is necessary
    to call recv() with the received data from the connection address so that
    the stream can process it.

    When the stream receives a correct data packet, it is queued in recv_queue.
    """

    def __init__(
        self,
        socket: socket,
        target: Address,
        recv_queue: Queue,
        window_size: int = WINDOW_SIZE,
    ):
        self.next_seq = SequenceNumber()
        self.expected = SequenceNumber()
        self.buffer: Dict[int, bytes] = {}
        self.timers: Dict[int, Timer] = {}
        self.window_semaphore = Semaphore(window_size)
        self.consecutive_interrupts = 0
        self.closing = False

        self.socket_lock = Lock()
        self.socket = socket
        self.target = target
        self.recv_queue = recv_queue

    def send(self, data: bytes):
        """
        Sends a data packet to the specified recipient. If the window
        size is reached, it blocks until an acknowledgment is received"""

        self.window_semaphore.acquire()

        packet = TransportDataPacket(self.next_seq._value, data)
        self._send_data_packet(packet)
        self.next_seq.increase()

    def _send_data_packet(self, packet: TransportDataPacket):
        """
        Sends the specified DataPacket and starts the corresponding timer."""

        self._start_timer_for(packet)
        self._send_packet(packet)

    def _resend_data_packet(self, packet: TransportDataPacket):
        """
        Resends the specified DataPacket. If the threshold of consecutive
        interrupts is reached, it is ignored. This allows the stream to
        stop when the connection is closed by the user."""

        try:
            self.timers.pop(packet.sequence).cancel()
        except KeyError:
            return


        self.consecutive_interrupts += 1
        if self.consecutive_interrupts >= DROP_THRESHOLD and self.closing:
            raise ConnectionError("Connection closed by user")

        self._send_data_packet(packet)

    def _start_timer_for(self, packet: TransportDataPacket):
        """
        Starts the timer to resend the specified DataPacket."""

        timer = Timer(TIMER, self._resend_data_packet, args=[packet])
        timer.start()
        self.timers[packet.sequence] = timer

    def handle_packet(self, data: bytes):
        """
        Processes the data received from the connection address.
        This must be able to be decoded into a Packet, otherwise
        it is ignored."""

        try:
            packet = TransportPacket.decode(data)
        except InvalidPacketException:
            return

        self.consecutive_interrupts = 0

        if isinstance(packet, TransportAckPacket):
            self._handle_ack(packet)
        elif isinstance(packet, TransportDataPacket):
            self._handle_data(packet)

    def _handle_ack(self, packet: TransportAckPacket):
        """
        Executes when an AckPacket is received. Cancels the timer
        corresponding to the data packet that has been received and releases
        a space in the window."""

        if self.timers.get(packet.sequence):
            self.timers.pop(packet.sequence).cancel()
            self.window_semaphore.release()

    def _send_packet(self, packet: TransportPacket):
        """
        Sends the specified Packet to the specified recipient."""

        self.socket_lock.acquire()
        self.socket.sendto(packet.encode(), self.target)
        self.socket_lock.release()

    def _send_ack(self, sequence: int):
        """
        Sends an acknowledgment for the packet with the specified sequence"""

        self._send_packet(TransportAckPacket(sequence))

    def _handle_data(self, packet: TransportDataPacket):
        """
        It is executed when a DataPacket is received. If the packet is received
        correctly, an acknowledgment is sent. If the packet is received in order,
        it is queued in recv_queue. If the packet is received out of order, it
        is saved in the buffer.

        When queuing a packet in recv_queue, it is checked if there are packets
        in the buffer that can also be queued."""

        if packet.length != len(packet.data):
            return


        self._send_ack(packet.sequence)

        if packet.sequence == self.expected.value:
            self.expected.increase()
            self._queue_packet(packet.data)
            self._queue_buffered()
        elif packet.sequence > self.expected.value:
            self.buffer[packet.sequence] = packet.data

    def _queue_packet(self, data: bytes):
        """
        Queues the specified data packet in recv_queue."""

        self.recv_queue.put((data, self.target))

    def _queue_buffered(self):
        """
        Enqueue all data packets in the buffer that can be queued in recv_queue."""

        while self.buffer.get(self.expected.value):
            self._queue_packet(self.buffer.pop(self.expected.value))
            self.expected.increase()

    def has_unacked_packets(self) -> bool:
        """
        Returns True if there are packets without acknowledgment."""

        return len(self.timers) > 0

    def close(self):
        """
        Prepares the stream to close. This implies canceling timers in
        case it is detected that the recipient has closed the connection."""

        self.closing = True
