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

    def close(self) -> None:
        """
        Cierra el socket
        """
        pass

    def send(self, data: bytes) -> None:
        """
        Envia los datos definidos en data a traves de la conexion
        """

        self.segmenter.segment(data)
        for packet in self.segmenter:
            self.socket.send(packet.encode())

    def recieve_file(self) -> bytes:
        print("self address:", self.socket.socket.getsockname())

        packet = self.socket.recv()

        # Chequear que sea de data
        packet = DataFPacket.decode_as_data(packet)
        self.segmenter.add_segment(packet)
        while len(packet.encode()) >= DATASIZE:
            packet = self.socket.recv()

            packet = DataFPacket.decode_as_data(packet)

            self.segmenter.add_segment(packet)

        return self.segmenter.desegment()
