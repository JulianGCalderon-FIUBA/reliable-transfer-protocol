from queue import Queue

from random import random
import threading
from typing import Tuple, Dict
import socket as skt
from lib.transport.consts import BUFSIZE, Address

from lib.transport.stream import ReliableStream

"""
IMPORTANTE:
- EL bufsize esta hardcodeado en 4096. Se podria hacer que sea configurable, pero
    idealmente los packets deberian poder ser segmentados en caso de que sean
    demasiado grandes.
- La implementación del stop and wait es un selective repeat, usando un
    window size de 1.
"""


class ReliableTransportProtocol:
    """
    Esta clase implementa envio de datos de forma confiable y en orden
    a traves de un socket UDP.

    La implementacion es connectionless, por lo que se debe indicar
    explicitamente el destinatario de cada paquete. Ademas, cada paquete
    recibido incluye la direccion del emisor."""

    def __init__(self):
        self.socket = skt.socket(skt.AF_INET, skt.SOCK_DGRAM)
        self.socket.settimeout(1)

        self.recv_queue = Queue()
        self.streams: Dict[Address, ReliableStream] = {}
        self.online = True

        self._spawn_reader()

    def recv_from(self) -> Tuple[bytes, Address]:
        """
        Recibe un paquete de datos de cualquier origen. Si aun no se ha
        recibido ningun paquete, se bloquea hasta que se reciba uno."""

        return self.recv_queue.get()

    def send_to(self, data: bytes, target: Address):
        """
        Envía un paquete de datos al destinatario especificado. Si
        aun no se ha recibido ningun paquete, se bloquea hasta que se
        reciba uno."""

        self._stream_for_address(target).send(data)

    def _spawn_reader(self):
        """
        Crea un thread que lee continuamente del socket y procesa los
        paquetes recibidos."""

        self.thread_handle = threading.Thread(target=self._reader)
        self.thread_handle.start()

    def _reader(self):
        """
        Lee continuamente del socket y procesa los paquetes recibidos."""

        socket = self.socket.dup()
        while self.online or self.has_unacked_packets():
            try:
                data, address = socket.recvfrom(BUFSIZE)
            except skt.error:
                continue

            # MANUAL PACKET LOSS
            while random() < 0.1:
                try:
                    data, address = socket.recvfrom(BUFSIZE)
                except skt.error:
                    continue
            # MANUAL PACKET LOSS

            self._stream_for_address(address).handle_packet(data)

    def _stream_for_address(self, address):
        """
        Cada conexion especifica es manejada por un objeto ReliableStream.
        Esta funcion devuelve el stream correspondiente a la direccion
        especificada. Si no existe, se crea uno nuevo.

        nota: Al no haber un handshake, es vulnerable a ataques syn flood.
        """

        if self.streams.get(address):
            return self.streams[address]

        self.streams[address] = ReliableStream(self.socket, address, self.recv_queue)

        return self._stream_for_address(address)

    def bind(self, address: Address):
        """
        Asocia el socket a la direccion especificada."""

        self.socket.bind(address)

    def has_unacked_packets(self):
        """
        Devuelve True si hay algun paquete sin confirmar."""

        return any(
            map(lambda stream: stream.has_unacked_packets(), self.streams.values())
        )

    def close(self):
        """
        Cierra el socket, liberando los recursos asociados a el.

        Antes de cerrar el socket, espera a que se hayan confirmado todos
        paquetes enviados. Si ocurre una gran cantidad consecutiva de timeouts
        sin recibir ningun paquete por parte del destinatario, se asume que
        la conexion se ha perdido y se cierra el socket. Esto evita que se
        quede esperando indefinidamente a que se confirme un paquete que
        nunca llegara, pero implica que los ultimos paquetes enviado pueden
        perderse."""

        self.online = False

        for stream in self.streams.values():
            stream.close()

        self.thread_handle.join()


class ReliableTransportClient(ReliableTransportProtocol):
    """
    Implementacion de ReliableTransportProtocol que simplifica el uso
    de la clase para el caso de un cliente.

    En lugar de tener que especificar el destinatario de cada paquete,
    se puede enviar y recibir datos directamente (ignorando aquellos
    paquetes que no provengan del destinatario especificado)."""

    def __init__(self, target: Address):
        super().__init__()
        self.target = target

    def send(self, data: bytes):
        """
        Envía un paquete de datos al destinatario especificado."""

        self.send_to(data, self.target)

    def recv(self) -> bytes:
        """
        Recibe un paquete de datos del destinatario especificado. Si
        aun no se ha recibido ningun paquete, se bloquea hasta que se
        reciba uno."""

        data, source = self.recv_from()
        if source == self.target:
            return data

        return self.recv()

    def set_target(self, target: Address):
        """
        Cambia el destinatario de los paquetes."""

        self.target = target


class ReliableTransportServer(ReliableTransportProtocol):
    """
    Implementacion de ReliableTransportProtocol que simplifica el uso
    de la clase para el caso de un servidor.
    Se bindea a una direccion especifica en construccion"""

    def __init__(self, address: Address):
        super().__init__()
        self.bind(address)
