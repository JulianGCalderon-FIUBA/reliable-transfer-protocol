from queue import Queue
from socket import socket
from threading import Semaphore, Timer
from typing import Dict
from lib.transport.consts import SEQUENCE_BYTES, TIMER, WINDOW_SIZE, Address

from lib.transport.packet import AckPacket, DataPacket, Packet


class SequenceNumber:
    """
    Los numeros de secuencia son numeros enteros de 16 bits sin signo,
    crecientes en cada paquete enviado. Al alcanzar el valor maximo, se
    reinicia a 0.
    """

    MAX_VALUE: int = SEQUENCE_BYTES**16 - 1

    def __init__(self):
        self._value = 0

    def increase(self):
        if self._value == self.MAX_VALUE:
            self._value = 0
        else:
            self._value += 1

    @property
    def value(self) -> int:
        return self._value


class ReliableStream:
    """
    Esta clase implementa envio de datos de forma confiable y en orden
    a traves de un socket UDP con un destinatario especifico.

    Debido a que el stream no lee ativamente del socket, es necesario
    llamar a recv() con los datos recibidos de la dirección de la conexión
    para que el stream pueda procesarlos.

    Cuando el stream recibe un paquete de datos correcto, este es
    encolado en recv_queue.

    Para enviar datos al otro extremo del stream, se debe llamar a send()
    con los datos a enviar.
    """

    def __init__(self, socket: socket, target: Address, recv_queue: Queue):
        self.next_seq = SequenceNumber()
        self.expected = SequenceNumber()
        self.buffer: Dict[int, bytes] = {}
        self.timers: Dict[int, Timer] = {}
        self.semaphore = Semaphore(WINDOW_SIZE)

        self.socket = socket
        self.target = target
        self.recv_queue = recv_queue

    def send(self, data: bytes):
        """
        Envía un paquete de datos al destinatario especificado."""
        self.semaphore.acquire()

        packet = DataPacket(self.next_seq._value, data)
        self._send_data_packet(packet)
        self.next_seq.increase()

    def _send_data_packet(self, packet: DataPacket):
        """
        Envia el DataPacket especificado y comienza el timer correspondiente."""

        self._send_packet(packet)
        self._start_timer_for(packet)

    def _resend_data_packet(self, packet: DataPacket):
        """
        Reenvia el DataPacket especificado."""

        self.timers.pop(packet.sequence).cancel()

        self._send_data_packet(packet)

    def _start_timer_for(self, packet: DataPacket):
        """
        Comienza el timer para reenviar el DataPacket especificado."""

        timer = Timer(TIMER, self._resend_data_packet, args=[packet])
        timer.start()
        self.timers[packet.sequence] = timer

    def recv(self, data: bytes):
        """
        Procesa los datos recibidos de la dirección de la conexión.
        Este debe poder ser decodificado en un Packet, en caso contrario
        se ignora."""

        packet = Packet.decode(data)
        if isinstance(packet, AckPacket):
            self._handle_ack(packet)
        elif isinstance(packet, DataPacket):
            self._handle_data(packet)

    def _handle_ack(self, packet: AckPacket):
        """
        Se ejecuta cuando se recibe un AckPacket. Cancela el timer
        correspondiente al paquete de datos que se ha recibido."""

        if self.timers.get(packet.sequence):
            self.timers.pop(packet.sequence).cancel()
            self.semaphore.release()

    def _send_packet(self, packet: Packet):
        """
        Envia el Packet especificado al destinatario especificado."""

        self.socket.sendto(packet.encode(), self.target)

    def _send_ack(self, sequence: int):
        """
        Envia un acknowledgment para el paquete con el numero de secuencia
        especificado al destinatario."""

        self._send_packet(AckPacket(sequence))

    def _handle_data(self, packet: DataPacket):
        """
        Se ejecuta cuando se recibe un DataPacket. Si el paquete se recibio
        correctamente, se envia un acknowledgment. Si el paquete se recibio
        en orden, se encola en recv_queue. Si el paquete se recibio fuera
        de orden, se guarda en el buffer.

        Al encolar un paquete en recv_queue, se comprueba si hay paquetes
        en el buffer que se pueden encolar tambien.
        """

        if packet.length != len(packet.data):
            return

        self._send_ack(packet.sequence)

        if packet.sequence == self.expected.value:
            self.expected.increase()
            self.queue_packet(packet.data)
            self.queue_buffered()
        elif packet.sequence > self.expected.value:
            self.buffer[packet.sequence] = packet.data

    def queue_packet(self, data: bytes):
        """
        Encola el paquete de datos especificado en recv_queue."""

        self.recv_queue.put((data, self.target))

    def queue_buffered(self):
        """
        Encola todos los paquetes de datos en el buffer que se pueden
        encolar en recv_queue."""

        while self.buffer.get(self.expected.value):
            self.queue_packet(self.buffer.pop(self.expected.value))
            self.expected.increase()
