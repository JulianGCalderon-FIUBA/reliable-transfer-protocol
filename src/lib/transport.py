from abc import ABC, abstractmethod
from socket import socket
from typing import Self
from lib.connection import SocketNotBindedException
from lib.constants import BUFFSIZE, SOCK_CONSTS
from lib.exceptions import IncorrectAnswerException
from lib.packet import Packet

class Transport(ABC):
    
    def __init__(self, socket: socket) -> Self:
        self.socket = socket
        self.timeout = SOCK_CONSTS.BASE_TIMEOUT

    @abstractmethod
    def sendto(self, packet: 'Packet', address: tuple[str, int]) -> tuple[str, int]:
        pass

    @abstractmethod
    def recvfrom(self) -> tuple['Packet', tuple[str, int]]:
        pass
    
    """
    Espera por la respuesta de un paquete, si hay un timeout o la respuesta no es la esperada devuelve una exepcion
    """
    def wait_for_answer(self, packet: 'Packet') -> tuple['Packet', tuple[str, int]]:
        self.socket.settimeout(self.timeout)

        possible_answer, address = self.recvfrom()

        if packet.is_expected_answer(possible_answer):
            return possible_answer, address
        
        raise IncorrectAnswerException(possible_answer)


    
    

class StopAndWait(Transport):
    
    def __init__(self, socket: socket, port: int, address="127.0.0.1") -> Self:
        super().__init__(socket, port, address)

    def recvfrom(self) -> tuple['Packet', tuple[str, int]]:
        stream, direccion = self.socket.recvfrom(BUFFSIZE)
        
        return Packet.decode(stream), direccion
    
    def sendto(self, data: 'Packet', address: tuple[str, int]) -> tuple['Packet', tuple[str, int]]:
        
        encoded_data = data.encode()
        sent = 0
        while sent < len(encoded_data):
            sent += self.socket.sendto(encoded_data, address)
            encoded_data = encoded_data[:sent]

        try:
            return self.wait_for_answer(data)
            
        except socket.timeout:
            #Por ahora lo dejo como para que trate de mandarlo ad infinitum
            self.send(data)
        except IncorrectAnswerException:
            #Puede ser un error, o no estar en orden. Checkear a futuro
            pass
        
        
