"""
Define la interfaz para la implementacion de conexiones de distinto tipo
"""
from abc import ABC
from lib.constants import DATASIZE, WILDCARD_ADDRESS
from lib.segmentation import Segmenter
from lib.packet import AckFPacket, DataFPacket, Packet, \
    ReadRequestPacket, WriteRequestPacket

from lib.transport.transport import Address, ReliableTransportProtocol


class ConnectionRFTP(ABC):
    def __init__(self, socket: ReliableTransportProtocol):
        self.socket = socket
        self.segmenter = Segmenter()

    """
    Espera por una nueva conexion y devuelve otra
    """

    def listen(self) -> tuple["Packet", Address]:
        packet, address = self.socket.recv_from()
        
        return Packet.decode(packet), address

    """
    Cierra el socket
    """

    def close(self) -> None:
        pass

    """
    Envia los datos definidos en data a traves de la conexion
    """

    def sendto(self, data, address: Address) -> None:
        self.segmenter.segment(data)
        packet = self.segmenter.get_next()
        while packet is not None:
            
            self.socket.send_to(packet.encode(), address)
            packet = self.segmenter.get_next()

    """
    Intenta recuperar un paquete de la conexion
    y la direccion de la cual lo recupero
    """

    def recieve_from(self) -> tuple[bytes, Address]:  # como string de bytes
        packet, address = self.socket.recv_from()
        
        return packet, address

    def send_handshake(self, packet: "Packet", address: tuple[str, int]):
        self.socket.send_to(packet.encode(), address)
        answer, address = self.recieve_from()
        answer = Packet.decode(answer)
        if packet.is_expected_answer(answer):
            return answer, address
        else:

            raise packet.get_fail_reason()  # type: ignore

    def answer_handshake(self, address: Address, ok=True):
        if ok:
            self.socket.send_to(AckFPacket(0).encode(), address)
        else:
            return

    """
    Inicia un upload de datos
    """

    def upload(
            self, filename: str, data: bytes, address: tuple[str, int]
            ) -> None:

        self.send_handshake(WriteRequestPacket(filename), address)
        self.sendto(data, address)

    """
    Inicia una descarga de datos
    """

    def download(self, filename: str, address: tuple[str, int]) -> bytes:
        self.send_handshake(ReadRequestPacket(filename), address)
        return self.recieve_file()

    def recieve_file(self) -> bytes:
        packet, _address = self.recieve_from()
        # Chekear que sea de data
        
        packet = DataFPacket.decode_as_data(packet)
        self.segmenter.add_segment(packet)
        while len(packet.encode()) >= DATASIZE:
            
            packet, _address = self.recieve_from()
            
            packet = DataFPacket.decode_as_data(packet)

            self.segmenter.add_segment(packet)

        return self.segmenter.desegment()


def bind_ephemeral_port(client_socket):
    client_socket.bind(
        (WILDCARD_ADDRESS, 4567)
    )  # the port here should be chosen at random
