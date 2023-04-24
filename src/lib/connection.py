"""
Define la interfaz para la implementacion de conexiones de distinto tipo
"""

from abc import ABC
from lib.constants import DATASIZE
from lib.exceptions import InvalidPacket
from lib.segmentation import Desegmenter, Segmenter
from lib.tftp_packet import (
    TFTPDataPacket,
    TFTPPacket,
)

from lib.transport.transport import (
    ReliableTransportClient,
)


class ConnectionRFTP(ABC):
    """
    Responible for sending and receiving files
    using RFTP protocol
    """

    def __init__(self, socket: ReliableTransportClient):
        self.socket = socket

    def send_file(self, file_path: str):
        """
        Sends a file using RFTP protocol, segmenting it
        into smaller packets"""

        segmenter = Segmenter(file_path)
        for packet in segmenter:
            packet = TFTPDataPacket(packet).encode()
            self.socket.send(packet)

    def receive_file(self, file_path: str):
        """
        Receives a file using RFTP protocol, desegmenting it
        into a single file"""

        desegmenter = Desegmenter(file_path)

        packet = self._recv_data()
        desegmenter.add_segment(packet)
        while len(packet) >= DATASIZE:
            packet = self._recv_data()
            desegmenter.add_segment(packet)

        desegmenter.close()

    def _recv_data(self):
        """
        Receives a data packet from the socket. Raises
        an exception if the packet is not a data packet"""

        packet = TFTPPacket.decode(self.socket.recv())

        if not isinstance(packet, TFTPDataPacket):
            raise InvalidPacket

        return packet.data
