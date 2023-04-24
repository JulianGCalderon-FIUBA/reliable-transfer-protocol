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
    def __init__(self, socket: ReliableTransportClient):
        self.socket = socket
        self.segmenter = Segmenter()

    def close(self):
        """
        Cierra el socket
        """

        pass

    def send_file(self, file_path: str):
        """
        Envia los datos definidos en data a traves de la conexion
        """

        self.segmenter.segment(file_path)
        for packet in self.segmenter:
            self.socket.send(packet.encode())

    def receive_file(self, file_path: str):
        packet = self.socket.recv()

        packet = DataFPacket.decode_as_data(packet)

        self.segmenter.desegment(file_path)

        self.segmenter.add_segment(packet)
        while packet.length >= DATASIZE:
            packet = self.socket.recv()

            packet = DataFPacket.decode_as_data(packet)

            self.segmenter.add_segment(packet)

        self.segmenter.close()
