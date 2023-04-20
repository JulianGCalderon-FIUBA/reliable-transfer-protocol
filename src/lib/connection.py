
"""
Define la interfaz para la implementacion de conexiones de distinto tipo
"""
from abc import ABC, abstractmethod
from typing import Self
from lib.constants import DATASIZE, WILDCARD_ADDRESS
from lib.segmentation import Segmenter
from lib.transport import StopAndWait
from lib.packet import AckPacket, Packet, ReadRequestPacket, WriteRequestPacket, DataPacket
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
        self.transport = StopAndWait(sckt, port, ip)
        self.segmenter = Segmenter(1)

    def recieve_from(self) -> bytes:
        
        packet, address = self.transport.recvfrom();
        
        #Chekear que sea de data
        self.transport.send_ack(packet, address)
        self.segmenter.add_segment(packet)
        while len(packet.encode()) >= DATASIZE:
            print("Recieved", packet.block)
            packet, address = self.transport.recvfrom();
            self.transport.send_ack(packet, address)
            self.segmenter.add_segment(packet)

        return self.segmenter.desegment()
        

    def listen(self) -> tuple['Packet', tuple[str, int]]:
        paquete, direccion = self.transport.recvfrom()
        
        return paquete, direccion
    def respond_handshake(self, address, status=True):
        self.transport.send_ack(DataPacket(0, ''), address)

    def close(self) -> None:
        self.transport.close()
        del self

    def sendto(self, data: bytes, address: tuple[str, int]) -> None:
        self.segmenter.segment(data)
        segment = self.segmenter.get_next()
        while segment != None:
            print("Sending: ", segment.block)
            answer, address = self.transport.sendto(segment, address)
            
            #Checkear que pasa si devuelve error o algo asi
            self.segmenter.remove_from_ack(answer)
            segment = self.segmenter.get_next()

    def send_handshake(self, packet: 'Packet', address: tuple[str, int]):
        self.transport.sendto(packet, address)
        print("Handshaked")




class SelectiveRepeatConnection(ConnectionRFTP):
    pass


def bind_ephemeral_port(client_socket):
    client_socket.bind((WILDCARD_ADDRESS, 4567)) # the port here should be chosen at random
