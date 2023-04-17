
"""
Define la interfaz para la implementacion de conexiones de distinto tipo
"""
from abc import ABC, abstractmethod
from typing import Self
from lib.constants import WILDCARD_ADDRESS
from packet import AckPacket, Packet, WriteRequestPacket
import socket


class ConnectionRFTP(ABC):
    """
    Bindea el socket efimero a la direccion especificada
    """
    @abstractmethod
    def bind(address: tuple):
        pass

    """
    Envia los datos definidos en data a traves de la conexion
    """
    @abstractmethod
    def send_to(self, data: 'Packet') -> None:
        pass
    
    """
    Intenta recuperar un paquete de la conexion
    """
    @abstractmethod
    def recieve_from(self) -> 'Packet': #como string de bytes
        pass



class StopAndWaitConnection(ConnectionRFTP):
    def __init__(self, ip: str, port: int) -> Self:
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.target_ip = ip
        self.target_port = port

        pass

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


    def send_data(self, packet: 'Packet') -> None:
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
