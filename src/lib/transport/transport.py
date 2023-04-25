from queue import Queue

import threading
from typing import Tuple, Dict
import socket as skt
from lib.transport.consts import BUFSIZE, WINDOW_SIZE, Address
from lib.transport.exceptions import SendingNoneData, InvalidAddress

from lib.transport.stream import ReliableStream


class ReliableTransportProtocol:

    """
    This class implements reliable and ordered data transmission over
    a UDP socket.

    The implementation is connectionless, so the recipient of each
    packet must be explicitly specified. In addition, each received
    packet includes the address of the sender."""

    def __init__(self, window_size: int = WINDOW_SIZE):
        self.socket = skt.socket(skt.AF_INET, skt.SOCK_DGRAM)
        self.socket.settimeout(1)
        self.window_size = window_size

        self.recv_queue = Queue()
        self.streams: Dict[Address, ReliableStream] = {}
        self.online = True

        self._spawn_reader()

    def recv_from(self) -> Tuple[bytes, Address]:
        """
        Receives a data packet from any source. If no packets have been
        received yet, it blocks until one is received."""

        return self.recv_queue.get()

    def send_to(self, data: bytes, target: Address):
        """Sends a data packet to the specified recipient. If no packets
        have been received yet, it blocks until one is received."""

        if data is None:
            raise SendingNoneData()

        if target[0] is None or target[1] is None:
            raise InvalidAddress()

        self._stream_for_address(target).send(data)

    def _spawn_reader(self):
        """
        Creates a thread that continuously reads from the socket and
        processes the received packets."""

        self.thread_handle = threading.Thread(target=self._reader)
        self.thread_handle.daemon = True
        self.thread_handle.start()

    def _reader(self):
        """
        Reads continuously from the socket and processes the received"""

        socket = self.socket.dup()
        while self.online or self._has_unacked_packets():
            try:
                data, address = socket.recvfrom(BUFSIZE)
            except skt.error:
                continue

            self._stream_for_address(address).handle_packet(data)

    def _stream_for_address(self, address):
        """
        Each specific connection is handled by a ReliableStream object.
        This function returns the stream corresponding to the specified
        address. If it does not exist, a new one is created.

        note: Since there is no handshake, it is vulnerable to syn flood"""

        return self.streams.setdefault(
            address,
            ReliableStream(
                self.socket.dup(), address, self.recv_queue, self.window_size
            ),
        )

    def bind(self, address: Address):
        """
        Asociates the socket to the specified address."""

        self.socket.bind(address)

    def _has_unacked_packets(self):
        """
        Returns True if there is any unconfirmed packet."""

        return any(
            map(lambda stream: stream.has_unacked_packets(), self.streams.values())
        )

    def close(self):
        """
        Closes the socket, releasing the resources associated with it.

        Before closing the socket, waits for all sent packets to be
        confirmed. If a large number of consecutive timeouts occur
        without receiving any packets from the recipient, it is assumed
        that the connection has been lost and the socket is closed. This
        prevents it from waiting indefinitely for a packet that will
        never arrive, but it means that the last sent packets may be
        lost."""

        self.online = False

        for stream in self.streams.values():
            stream.close()

        self.thread_handle.join()

        self.socket.close()


class ReliableTransportClient(ReliableTransportProtocol):

    """
    Implementation of ReliableTransportProtocol that simplifies the use
    of the class for the case of a client.

    Instead of having to specify the recipient of each packet, you can
    send and receive data directly (ignoring those packets that do not
    come from the specified recipient)."""

    def __init__(self, target: Address):
        if target[0] is None or target[1] is None:
            raise InvalidAddress()

        super().__init__()
        self.target = target

    def send(self, data: bytes):
        """
        Sends a data packet to the specified recipient."""

        self.send_to(data, self.target)

    def recv(self) -> bytes:
        """
        Receives a data packet from the specified recipient. If no
        packets have been received yet, it blocks until one is
        received."""

        data, source = self.recv_from()
        if source == self.target:
            return data

        return self.recv()

    def set_target(self, target: Address):
        """
        Changes the recipient of the packets."""

        self.target = target


class ReliableTransportServer(ReliableTransportProtocol):

    """
    Implementation of ReliableTransportProtocol that simplifies the use
    of the protocol for server process. It binds to a specific
    address when it is constructed."""

    def __init__(self, address: Address):
        if address[0] is None or address[1] is None:
            raise InvalidAddress()

        super().__init__()
        self.bind(address)
