from abc import ABC, abstractmethod
import socket
from typing import Tuple

Address = Tuple[str, int]


class ReliableTransportProtocol(ABC):
    """
    Clase base para un protocolo de transporte confiable.

    Este protocolo es capaz de enviar y recibir paquetes de datos de forma
    confiable y en orden.

    Es un protocolo connectionless, por lo que no se establece una conexion
    entre el cliente y el servidor. Cada paquete de datos enviado debe
    contener la direccion del destinatario. Cada paquete de datos recibido
    debe contener la direccion del remitente.
    """

    def __init__(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    @abstractmethod
    def send_to(self, data: bytes, address: Address):
        """
        Envía un paquete de datos al destinatario especificado."""
        pass

    @abstractmethod
    def recv_from() -> Tuple[bytes, Address]:
        """
        Recibe un paquete de datos de la cola. Si no hay paquetes disponibles, se bloquea
        hasta que se reciba uno."""
        pass


class ReliableTransportClientProtocol(ReliableTransportProtocol):
    """
    Extensión de ReliableTransportProtocol para un cliente. Permite establecer
    un destino para el envío de paquetes de datos, para que no sea necesario
    especificar el destino en cada llamada a send."""

    def __init__(self, target):
        super().__init__()
        self.target = target

    def send(self, data: bytes):
        self.send_to(data, self.target)

    def set_target(self, target):
        self.target = target


class ReliableTransportServerProtocol(ReliableTransportProtocol):
    """
    Extensión de ReliableTransportProtocol para un servidor. Permite bindear
    el socket a una dirección y puerto."""

    def __init__(self, source):
        super().__init__()
        self.socket.bind(source)
