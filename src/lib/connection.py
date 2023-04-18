
"""
Define la interfaz para la implementacion de conexiones de distinto tipo
"""
from abc import ABC, abstractmethod
from typing import Self
from lib.constants import WILDCARD_ADDRESS, BUFFSIZE
from packet import AckPacket, Packet, WriteRequestPacket, DataPacket
import socket

class SocketNotBindedException(Exception):
    pass

class ConnectionRFTP(ABC):
    """
    Bindea el socket efimero a la direccion especificada
    """
    @abstractmethod
    def bind(self, address: tuple[str, int]) -> None:
        pass
    
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
    def send(self, data: 'Packet') -> None:
        pass
    
    """
    Intenta recuperar un paquete de la conexion y la direccion de la cual lo recupero
    """
    @abstractmethod
    def recieve_from(self) -> tuple['Packet', tuple[str, int]]: #como string de bytes
        pass



class StopAndWaitConnection(ConnectionRFTP):
    def __init__(self, ip: str, port: int) -> Self:
        self.socket: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.binded_addr: tuple[str, int] = None
        self.target_ip: str = ip
        self.target_port: int = port

        pass

    def bind(self, address: tuple[str, int]) -> None:
        try:
            self.socket.bind(address)
            self.binded_addr = address
        except Exception as e:
            print(e)
            
    def is_binded(self) -> bool:
        return self.binded_addr != None

    def listen(self) -> tuple['Packet', Self]:
        paquete, direccion = self.recieve_from()
        
        return paquete, Self(direccion[0], direccion[1])

    def recieve_from(self) -> tuple['Packet', tuple[str, int]]:
        if not self.is_binded():
            raise SocketNotBindedException()
        
        stream, direccion = self.socket.recvfrom(BUFFSIZE)

        return Packet.decode(stream), direccion

    def close(self) -> None:
        self.socket.close()
        del self

    def send(self, data: 'Packet') -> None:
        if not self.is_binded():
            raise SocketNotBindedException()
        encoded_data = data.encode()
        sent = 0
        while sent < len(encoded_data):
            sent += self.socket.sendto(encoded_data, (self.target_ip, self.target_port))
            encoded_data = encoded_data[:sent]
            
    def send_wrq(self, packet: 'WriteRequestPacket') -> None:
        # enviar Paquete
        packet_aux = packet.encode()
        self.socket.sendto(packet_aux, (self.target_ip, self.target_port))
        # esperar respuesta
        old_ip = self.target_ip
        while old_ip == self.target_ip:
            data, addr = self.self.socket.recvfrom()
            if addr[0] != self.target_ip:
                # received packet from unexpected IP
                continue
            if not isinstance(Packet.decode(data), AckPacket):
                self.socket.sendto(packet_aux, (self.target_ip, self.target_port))
                continue
            self.target_port = addr[1]


    def send_data(self, packet: 'DataPacket') -> None:
        # enviar Paquete
        packet_aux = packet.encode()
        self.socket.sendto(packet_aux, (self.target_ip, self.target_port))
        # esperar ack
        data, addr = self.socket.recvfrom()

        # reenviar si es necesario
        while(not isinstance(Packet.decode(data), AckPacket)):
            self.socket.sendto(packet_aux, (self.target_ip, self.target_port))
            data = self.socket.recvfrom()



class SelectiveRepeatConnection(ConnectionRFTP):
    pass


def bind_ephemeral_port(client_socket):
    client_socket.bind((WILDCARD_ADDRESS, 4567)) # the port here should be chosen at random
