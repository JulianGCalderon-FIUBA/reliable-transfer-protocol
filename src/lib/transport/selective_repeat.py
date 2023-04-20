from queue import Queue
from random import random
import threading
from typing import Tuple, Dict, List

from lib.transport.packet import MAX_SEQUENCE, AckPacket, DataPacket, Packet
from lib.transport.transport import (
    BUFSIZE,
    TIMER_DURATION,
    Address,
    ReliableTransportClientProtocol,
    ReliableTransportProtocol,
    ReliableTransportServerProtocol,
)

WINDOW_SIZE = 30

"""
IMPORTANTE:
- Actualmente no se esta utilizando el window size. Se debe limitar la cantidad
    de paquetes que se pueden enviar sin recibir un acknowledgment.
- EL bufsize esta hardcodeado en 4096. Se podria hacer que sea configurable, pero
    idealmente los packets deberian poder ser segmentados en caso de que sean
    demasiado grandes.
- La duracion del timer esta hardcodeada en 0.1 segundos. Este valor es arbitrario
    y se podria cambiar.
- Para limitar la cantidad de paquetes que se pueden enviar sin recibir un
    acknowledgment, se utiliza un while loop en el metodo send_to. Esto es
    ineficiente, ya que se pierde procesamiento. Deberia cambiarse por algun tipo
    sincronización
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

    queue: "Queue" = Queue()
    next_sequence: Dict[Address, int] = {}
    expected_sequence: Dict[Address, int] = {}

    received_packets: Dict[Address, List[int]] = {}
    running_timers: Dict[Address, Dict[int, threading.Timer]] = {}
    unordered_packets: Dict[Address, List[(DataPacket)]] = {}

    def __init__(self):
        super().__init__()

        self.start_read_thread()

    def recv_from(self) -> Tuple[bytes, Address]:
        """
        Recibe un paquete de datos de la cola. Si no hay paquetes disponibles,
        se bloquea hasta que se reciba uno."""
        return self.queue.get()

    def send_to(self, data: bytes, target: Address):
        """
        Envia un paquete de datos al destinatario especificado."""

        data_packet = DataPacket(self.get_next_seq(target), data)

        while len(self.get_timers(target).keys()) >= WINDOW_SIZE:
            print("Waiting for unaknowledge packets...")
            continue

        print(f"Unaknowledge packets: {len(self.get_timers(target).keys())}")

        self.send_data_packet(data_packet, target)

        self.increase_next_seq(target)

    def send_data_packet(self, packet: DataPacket, target: Address):
        """
        Envia un paquete de datos al destinatario especificado. Iniciando un
        timer para reenviar el paquete en caso de que no se reciba un
        acknowledgment."""

        self.start_timer(packet, target)

        self.socket.sendto(packet.encode(), target)

    def start_timer(self, packet: DataPacket, target: Address):
        """
        Inicia un timer y lo agrega a la lista de timers activos."""

        timer = threading.Timer(
            TIMER_DURATION, lambda: self.send_data_packet(packet, target)
        )
        timer.start()
        self.get_timers(target)[packet.sequence] = timer

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

            packet = Packet.decode(data)
            if isinstance(packet, AckPacket):
                self.on_ack_packet(packet, address)

            elif isinstance(packet, DataPacket):
                self.on_data_packet(packet, address)

    def on_ack_packet(self, packet: AckPacket, source: Address):
        """
        Se ejecuta cuando se recibe un acknowledgment. Cancela el timer
        correspondiente al paquete de datos que se recibio el acknowledgment."""

        try:
            self.get_timers(source).pop(packet.sequence).cancel()
        except KeyError:
            pass

    def on_data_packet(self, packet: DataPacket, source: Address):
        """
        Se ejecuta cuando se recibe un paquete de datos. Verifica que el
        paquete sea correcto, y en caso de serlo, lo encola.

        En caso de recibir un paquete fuera de orden, lo guarda en un buffer
        para ser encolado en cuanto se reciban los paquete que lo preceden."""

        if packet.length != len(packet.data):
            return

        self.socket.sendto(AckPacket(packet.sequence).encode(), source)

        if packet.sequence in self.get_received(source):
            return

        self.add_received(source, packet.sequence)

        if self.get_expected_seq(source) == packet.sequence:
            self.queue.put((packet.data, source))
            self.increase_expected_seq(source)
            self.queue_buffered_packets(source)
        else:
            self.get_buffered(source).append(packet)

    def queue_buffered_packets(self, source: Address):
        """
        Si hay paquetes en el buffer que pueden ser encolados, los encola"""

        self.get_buffered(source).sort(key=lambda packet: packet.sequence, reverse=True)

        for i in range(len(self.get_buffered(source)) - 1, -1, -1):
            packet = self.get_buffered(source)[i]

            if self.get_expected_seq(source) == packet.sequence:
                self.get_buffered(source).pop(i)
                self.queue.put((packet.data, source))
                self.increase_expected_seq(source)

    def add_received(self, source: Address, id: int):
        """
        Agrega un paquete recibido a la lista de paquetes recibidos.
        Se mantiene una ventana de paquetes recibidos para unicamente
        llevar un registro de los ultimos paquetes recibidos."""

        if len(self.get_received(source)) <= id % WINDOW_SIZE:
            self.get_received(source).append(id)
        else:
            self.get_received(source)[id % WINDOW_SIZE] = id

    def get_timers(self, target: Address) -> Dict[int, threading.Timer]:
        return self.running_timers.setdefault(target, {})

    def get_received(self, source: Address) -> List[int]:
        return self.received_packets.setdefault(source, [])

    def get_buffered(self, source: Address) -> List[DataPacket]:
        return self.unordered_packets.setdefault(source, [])

    def get_expected_seq(self, source: Address) -> int:
        return self.expected_sequence.setdefault(source, 0)

    def get_next_seq(self, target: Address) -> int:
        return self.next_sequence.setdefault(target, 0)

    def increase_next_seq(self, target: Address):
        self.next_sequence[target] = self.wrapped_increase(self.next_sequence[target])

    def increase_expected_seq(self, source: Address):
        self.expected_sequence[source] = self.wrapped_increase(
            self.expected_sequence[source]
        )

    def wrapped_increase(self, number: int) -> int:
        """
        Incrementa un numero de secuencia, y si este llega al maximo,
        lo reinicia a 0"""

        if number == MAX_SEQUENCE:
            return 0

        return number + 1


class SelectiveRepeatClientProtocol(
    ReliableTransportClientProtocol, SelectiveRepeatProtocol
):
    pass


class SelectiveRepeatServerProtocol(
    ReliableTransportServerProtocol, SelectiveRepeatProtocol
):
    pass
