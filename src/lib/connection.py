"""
Define la interfaz para la implementacion de conexiones de distinto tipo
"""

from abc import ABC
from lib.constants import DATASIZE
from lib.segmentation import Segmenter
from lib.packet import (
    DataFPacket,
)

from lib.transport.transport import (
    ReliableTransportClient,
)


class ConnectionRFTP(ABC):
    def __init__(self, socket: ReliableTransportClient, file_path: str):
        self.socket = socket
        self.segmenter = Segmenter(file_path)

    def close(self):
        """
        Cierra el socket
        """

        pass

    def send_file(self):
        """
        Envia los datos definidos en data a traves de la conexion
        """

        self.segmenter.segment()
        for packet in self.segmenter:
            self.socket.send(packet.encode())

    def recieve_file(self):
        packet = self.socket.recv()

        self.segmenter.desegment()
        packet = DataFPacket.decode_as_data(packet)

        self.segmenter.add_segment(packet)

        while packet.length >= DATASIZE:
            packet = self.socket.recv()

            packet = DataFPacket.decode_as_data(packet)

            self.segmenter.add_segment(packet)
