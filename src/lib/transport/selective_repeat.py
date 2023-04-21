from queue import Queue
from random import random
import threading
from typing import Tuple, Dict

from lib.transport.stream import Stream
from lib.transport.transport import (
    BUFSIZE,
    Address,
    ReliableTransportClientProtocol,
    ReliableTransportProtocol,
    ReliableTransportServerProtocol,
)

WINDOW_SIZE = 30

"""
IMPORTANTE:
- EL bufsize esta hardcodeado en 4096. Se podria hacer que sea configurable, pero
    idealmente los packets deberian poder ser segmentados en caso de que sean
    demasiado grandes.
- La duracion del timer esta hardcodeada en 0.1 segundos. Este valor es arbitrario
    y se podria cambiar.
- Para limitar la cantidad de paquetes que se pueden enviar sin recibir un
    acknowledgment, se utiliza un while loop en el metodo send_to. Esto es
    ineficiente, ya que se pierde procesamiento. Deberia cambiarse por algun tipo
    sincronización
- El protocolo NO ES thread safe. (inclusive la implementación puede fallar bajo
    ciertas condiciones)
"""


class SelectiveRepeatProtocol(ReliableTransportProtocol):
    """
    Implementacion del protocolo un protocolo de transporte confiable,
    utilizando el algoritmo de Selective Repeat.

    Este protocolo es capaz de enviar y recibir paquetes de datos de forma
    confiable y en orden. Para cada paquete de datos enviado, se espera un
    acknowledgment del mismo. Si el acknowledgment no es recibido en un tiempo
    determinado, se reenvia el paquete de datos.

    Es un protocolo connectionless, por lo que no se establece una conexion
    entre el cliente y el servidor. Cada paquete de datos enviado debe
    contener la direccion del destinatario. Cada paquete de datos recibido
    debe contener la direccion del remitente."""

    def __init__(self):
        super().__init__()

        self.queue = Queue()
        self.streams: Dict[Address, Stream] = {}

        self.start_read_thread()

    def recv_from(self) -> Tuple[bytes, Address]:
        """
        Recibe un paquete de datos de la cola. Si no hay paquetes disponibles,
        se bloquea hasta que se reciba uno."""
        return self.queue.get()

    def send_to(self, data: bytes, target: Address):
        """
        Envia un paquete de datos al destinatario especificado."""
        self.stream_for_address(target).send(data)

    def start_read_thread(self):
        """
        Inicia un thread para leer los paquetes recibidos."""

        self.thread_handle = threading.Thread(target=self.read_thread)
        self.thread_handle.start()

    def read_thread(self):
        """
        Inicia un thread para leer los paquetes recibidos.
        Este thread se encarga de verificar que los paquetes recibidos sean
        correctos, y de enviar los acknowledgment correspondientes.

        Los paquetes recibidos incorrectos son descartados, mientras que los
        paquetes recibidos correctamente son encolados para ser procesados por
        el thread principal en el momento adecuado."""

        while True:
            data, address = self.socket.recvfrom(BUFSIZE)

            # MANUAL PACKET LOSS
            while random() < 0.1:
                data, address = self.socket.recvfrom(BUFSIZE)
            # MANUAL PACKET LOSS

            self.stream_for_address(address).recv(data)

    def stream_for_address(self, address):
        if self.streams.get(address):
            return self.streams[address]

        self.streams[address] = Stream(self.socket, address, self.queue)

        return self.stream_for_address(address)


class SelectiveRepeatClientProtocol(
    ReliableTransportClientProtocol, SelectiveRepeatProtocol
):
    pass


class SelectiveRepeatServerProtocol(
    ReliableTransportServerProtocol, SelectiveRepeatProtocol
):
    pass
