from queue import Queue
from random import random
import threading
from typing import Dict, Tuple
from lib.transport.packet import AckPacket, DataPacket, Packet
from lib.transport.transport import (
    Address,
    ReliableTransportClientProtocol,
    ReliableTransportProtocol,
    ReliableTransportServerProtocol,
)

BUFSIZE = 4096
TIMER_DURATION = 0.1
WINDOW_SIZE = 10


class StopAndWaitProtocol(ReliableTransportProtocol):
    """
    Implementacion del protocolo un protocolo de transporte confiable,
    utilizando el algoritmo de Stop and Wait.

    Este protocolo es capaz de enviar y recibir paquetes de datos de forma
    confiable y en orden. Para cada paquete de datos enviado, se espera un
    acknowledgment del mismo. Si el acknowledgment no es recibido en un tiempo
    determinado, se reenvia el paquete de datos.

    Es un protocolo connectionless, por lo que no se establece una conexion
    entre el cliente y el servidor. Cada paquete de datos enviado debe
    contener la direccion del destinatario. Cada paquete de datos recibido
    debe contener la direccion del remitente."""

    next_seq: Dict[Address, bool] = {}
    expected_seq: Dict[Address, bool] = {}
    queue: "Queue" = Queue()

    def __init__(self):
        super().__init__()

        self.start_read_thread()

    def recv_from(self) -> Tuple[bytes, Address]:
        """
        Recibe un paquete de datos de la cola. Si no hay paquetes disponibles, se bloquea
        hasta que se reciba uno."""
        return self.queue.get()

    def send_to(self, data: bytes, target: Address):
        """
        Envía un paquete de datos al destinatario especificado."""

        data_packet = DataPacket(self.get_next_seq(target), data)

        self.send_data_packet(data_packet, target)

        self.increase_next_seq(target)

    def send_data_packet(self, packet: DataPacket, target: Address):
        """
        Envía un paquete de datos al destinatario especificado.

        Si el paquete de datos no es recibido en un tiempo determinado, se reenvia el
        paquete de datos.

        El timer se inicia en el mismo thread que el que envia el paquete de datos,
        por lo que la operacion es bloqueante"""

        self.start_timer(packet, target)

        self.socket.sendto(packet.encode(), target)

        self.timer.start()
        self.timer.join()

    def start_timer(self, data_packet: DataPacket, target: Address):
        """
        Inicia un timer que se encarga de reenviar el paquete de datos si no es recibido
        en un tiempo determinado."""
        self.timer = threading.Timer(
            TIMER_DURATION, lambda: self.send_data_packet(data_packet, target)
        )

    def start_read_thread(self):
        """
        Inicia un thread que se encarga de leer los paquetes recibidos"""
        self.thread_handle = threading.Thread(target=self.read_thread)
        self.thread_handle.start()

    def read_thread(self):
        """
        Thread que se encarga de leer los paquetes recibidos,
        enviando un Acknowledgment para cada paquete de datos recibido.

        Si el paquete recibido es un Acknowledgment, se cancela el timer asociado.
        Si el paquete recibido es un paquete de datos, se envia un Acknowledgment
        y se agrega el paquete a la cola de paquetes recibidos."""

        while True:
            data, address = self.socket.recvfrom(BUFSIZE)

            # MANUAL PACKET LOSS
            while random() < 0.1:
                data, address = self.socket.recvfrom(BUFSIZE)
            # MANUAL PACKET LOSS

            packet = Packet.decode(data)
            if isinstance(packet, AckPacket):
                self.on_ack_packet(packet, address)

            elif isinstance(packet, DataPacket):
                self.on_data_packet(packet, address)

    def on_ack_packet(self, packet: AckPacket, source: Address):
        """
        Se ejecuta cuando se recibe un Acknowledgment.

        Si el numero de secuencia del Acknowledgment corresponde al numero de secuencia
        del paquete de datos enviado, se cancela el timer asociado al paquete de datos.
        """

        if self.get_next_seq(source) == packet.sequence:
            self.timer.cancel()

    def on_data_packet(self, packet: DataPacket, source: Address):
        """
        Se ejecuta cuando se recibe un paquete de datos.

        Si el numero de secuencia del paquete de datos recibido corresponde al numero de
        secuencia esperado, se envia un Acknowledgment y se agrega el paquete de datos
        a la cola de paquetes recibidos."""

        if packet.length != len(packet.data):
            return

        self.socket.sendto(AckPacket(packet.sequence).encode(), source)

        if self.get_expected_seq(source) == packet.sequence:
            self.queue.put((packet.data, source))
            self.increase_expected_seq(source)

    def increase_next_seq(self, address: Address):
        self.next_seq[address] = not self.next_seq[address]

    def increase_expected_seq(self, address: Address):
        self.expected_seq[address] = not self.expected_seq[address]

    def get_next_seq(self, address: Address) -> int:
        return self.next_seq.setdefault(address, False)

    def get_expected_seq(self, address: Address) -> int:
        return self.expected_seq.setdefault(address, False)


class StopAndWaitClientProtocol(ReliableTransportClientProtocol, StopAndWaitProtocol):
    pass


class StopAndWaitServerProtocol(ReliableTransportServerProtocol, StopAndWaitProtocol):
    pass
