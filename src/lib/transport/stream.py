from queue import Queue
from socket import socket
from threading import Semaphore, Timer
from typing import Dict
from lib.transport.consts import DROP_THRESHOLD, TIMER, WINDOW_SIZE, Address

from lib.transport.transport_packet import (
    SEQUENCE_BYTES,
    TransportAckPacket,
    TransportDataPacket,
    InvalidPacketException,
    TransportPacket,
)


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

    Debido a que el stream no lee activamente del socket, es necesario
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
        self.window_semaphore = Semaphore(WINDOW_SIZE)
        self.consecutive_interrupts = 0
        self.closing = False

        self.socket = socket
        self.target = target
        self.recv_queue = recv_queue

    def send(self, data: bytes):
        """
        Envía un paquete de datos al destinatario especificado. Si
        se alcanza el tamaño de la ventana, se bloquea hasta que se
        reciba un acknowledgment para un paquete enviado."""
        self.window_semaphore.acquire()

        packet = TransportDataPacket(self.next_seq._value, data)
        self._send_data_packet(packet)
        self.next_seq.increase()

    def _send_data_packet(self, packet: TransportDataPacket):
        """
        Envia el DataPacket especificado y comienza el timer correspondiente."""

        self._start_timer_for(packet)
        self._send_packet(packet)

    def _resend_data_packet(self, packet: TransportDataPacket):
        """
        Reenvia el DataPacket especificado. Si se alcanza el umbral de
        interrupciones consecutivas, se ignora. Esto permite que el
        stream frene ante el cierre de la conexión por parte del
        destinatario."""

        self.timers.pop(packet.sequence).cancel()

        self.consecutive_interrupts += 1
        if self.consecutive_interrupts >= DROP_THRESHOLD and self.closing:
            return

        self._send_data_packet(packet)

    def _start_timer_for(self, packet: TransportDataPacket):
        """
        Comienza el timer para reenviar el DataPacket especificado."""

        timer = Timer(TIMER, self._resend_data_packet, args=[packet])
        timer.start()
        self.timers[packet.sequence] = timer

    def handle_packet(self, data: bytes):
        """
        Procesa los datos recibidos de la dirección de la conexión.
        Este debe poder ser decodificado en un Packet, en caso contrario
        se ignora."""

        try:
            packet = TransportPacket.decode(data)
        except InvalidPacketException:
            return

        self.consecutive_interrupts = 0

        if isinstance(packet, TransportAckPacket):
            self._handle_ack(packet)
        elif isinstance(packet, TransportDataPacket):
            self._handle_data(packet)

    def _handle_ack(self, packet: TransportAckPacket):
        """
        Se ejecuta cuando se recibe un AckPacket. Cancela el timer
        correspondiente al paquete de datos que se ha recibido y libera
        un espacio en la ventana."""

        if self.timers.get(packet.sequence):
            self.timers.pop(packet.sequence).cancel()
            self.window_semaphore.release()

    def _send_packet(self, packet: TransportPacket):
        """
        Envia el Packet especificado al destinatario especificado."""

        self.socket.sendto(packet.encode(), self.target)

    def _send_ack(self, sequence: int):
        """
        Envia un acknowledgment para el paquete con el numero de secuencia
        especificado al destinatario."""

        self._send_packet(TransportAckPacket(sequence))

    def _handle_data(self, packet: TransportDataPacket):
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
            self._queue_packet(packet.data)
            self._queue_buffered()
        elif packet.sequence > self.expected.value:
            self.buffer[packet.sequence] = packet.data

    def _queue_packet(self, data: bytes):
        """
        Encola el paquete de datos especificado en recv_queue."""

        self.recv_queue.put((data, self.target))

    def _queue_buffered(self):
        """
        Encola todos los paquetes de datos en el buffer que se pueden
        encolar en recv_queue."""

        while self.buffer.get(self.expected.value):
            self._queue_packet(self.buffer.pop(self.expected.value))
            self.expected.increase()

    def has_unacked_packets(self) -> bool:
        """
        Retorna True si hay paquetes sin acknowledgment."""

        return len(self.timers) > 0

    def close(self):
        """
        Prepara el cierra del stream. Esto implica cancelar timers en
        caso de que se detecte que el destinatario ha cerrado la conexión."""

        self.closing = True
