"""
Define la interfaz para la implementacion de conexiones de distinto tipo
"""

from abc import ABC
from lib.constants import DATASIZE
from lib.segmentation import Desegmenter, Segmenter
from lib.packet import (
    DataFPacket,
)

from lib.transport.transport import (
    ReliableTransportClient,
)


class ConnectionRFTP(ABC):
    def __init__(self, socket: ReliableTransportClient):
        self.socket = socket

    def send_file(self, file_path: str):
        """
        Envia los datos definidos en data a traves de la conexion
        """

        segmenter = Segmenter(file_path)
        for packet in segmenter:
            self.socket.send(packet.encode())

    def receive_file(self, file_path: str):
        packet = self.socket.recv()

        packet = DataFPacket.decode_as_data(packet)

        desegmenter = Desegmenter(file_path)

        desegmenter.add_segment(packet)
        while packet.length >= DATASIZE:
            packet = self.socket.recv()

            packet = DataFPacket.decode_as_data(packet)

            desegmenter.add_segment(packet)

        desegmenter.close()
