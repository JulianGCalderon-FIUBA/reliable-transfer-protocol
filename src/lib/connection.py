
"""
Define la interfaz para la implementacion de conexiones de distinto tipo
"""
from abc import ABC, abstractmethod
from typing import Self
from lib.constants import WILDCARD_ADDRESS, BUFFSIZE
from lib.transport import StopAndWait
from packet import AckPacket, Packet, ReadRequestPacket, WriteRequestPacket, DataPacket
import socket

class SocketNotBindedException(Exception):
    pass

class ConnectionRFTP(ABC): 

    
    
    """
    Espera por una nueva conexion y devuelve otra
    """
    @abstractmethod
    def listen(self) -> tuple['Packet', Self]:
        pass

    """
    Cierra el socket
    """
    @abstractmethod
    def close(self) -> None:
        pass

    """
    Envia los datos definidos en data a traves de la conexion
    """
    @abstractmethod
    def sendto(self, data: any, address: tuple[str, int]) -> None:
        pass
    
    """
    Intenta recuperar un paquete de la conexion y la direccion de la cual lo recupero
    """
    @abstractmethod
    def recieve_from(self) -> bytes: #como string de bytes
        pass
    
    @abstractmethod
    def send_handshake(self, packet: 'Packet', address: tuple[str, int]):
        pass

    """
    Inicia un upload de datos
    """
    def upload(self, filename: str, data: bytes, address: tuple[str, int]) -> None:
        self.send_handshake(WriteRequestPacket(filename), address)
        self.sendto(data, address)

    """
    Inicia una descarga de datos
    """
    def download(self, filename: str, address: tuple[str, int]) -> bytes:
        self.send_handshake(ReadRequestPacket(filename), address)
        return self.recieve_from()
        



class StopAndWaitConnection(ConnectionRFTP):

    def __init__(self, ip: str, port: int) -> Self:
        
        sckt = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sckt.bind((ip, port))
        self.transport = StopAndWait(sckt)

    def recieve_from(self) -> bytes:
        #Aca tiene que haber un juego con el segmenter y demas
        pass

    def listen(self) -> tuple['Packet', tuple[str, int]]:
        paquete, direccion = self.recieve_from()
        
        return paquete, direccion

    def close(self) -> None:
        self.transport.close()
        del self

    def sendto(self, data: bytes, address: tuple[str, int]) -> None:
        #segments = self.segment_manager.create_and_return(data)

        segments = []
        for segment in segments:
            self.transport.sendto(segment, address)

    def send_handshake(self, packet: 'Packet', address: tuple[str, int]):
        self.transport.sendto(packet, address)




class SelectiveRepeatConnection(ConnectionRFTP):
    pass


def bind_ephemeral_port(client_socket):
    client_socket.bind((WILDCARD_ADDRESS, 4567)) # the port here should be chosen at random
