from abc import ABC
from enum import IntEnum, auto

from lib.transport.exceptions import InvalidPacketException


SEQUENCE_BYTES = 2
LENGTH_BYTES = 2
ENDIAN = "big"


class _CODES(IntEnum):
    """
    Códigos de operación para distinguir los paquetes."""

    ACK = auto()
    DATA = auto()


class TransportPacket(ABC):
    """
    Clase base para los paquetes."""

    @classmethod
    def decode(cls, data: bytes) -> "TransportPacket":
        """
        Decodifica un paquete a partir de un stream de bytes.
        La instancia del paquete dependerá del código de operación."""

        opcode = int.from_bytes(data[:2], ENDIAN)
        data = data[2:]

        for subclass in cls.__subclasses__():
            if subclass._opcode() == opcode:
                return subclass.decode(data)

        raise InvalidPacketException()

    @classmethod
    def _opcode(cls) -> int:
        """
        Codigo de operacion del paquete."""
        return 0

    def encode(self) -> bytes:
        """
        Codifica el paquete a un stream de bytes.
        El stream de bytes comienza con el codigo de operacion
        y luego los headers especificos para cada subclase.
        La implementación base unicamente codifica el codigo de
        operacion"""

        return self._opcode().to_bytes(2, ENDIAN)


class TransportAckPacket(TransportPacket):
    """
    Paquete de acknowledgment del paquete DATA."""

    def __init__(self, sequence: int):
        """
        Se define con un numero de secuencia.
        Corresponde al numero de secuencia del paquete DATA
        al que se esta respondiendo."""
        self.sequence = sequence

    @classmethod
    def _opcode(cls) -> int:
        return _CODES.ACK

    @classmethod
    def decode(cls, stream: bytes) -> "TransportAckPacket":
        id = int.from_bytes(stream[:2], ENDIAN)

        return cls(id)

    def encode(self) -> bytes:
        return super().encode() + self.sequence.to_bytes(2, ENDIAN)


class TransportDataPacket(TransportPacket):
    """
    Paquete de datos."""

    def __init__(self, sequence: int, data: bytes):
        """
        Se define con un numero de secuencia el cual identificara el paquete,
        y con los datos a enviar. El paquete tambien contiene la longitud de los
        datos a enviar, para verificar que el paquete se haya enviado correctamente"""
        self.sequence = sequence
        self.length = len(data)
        self.data = data

    @classmethod
    def _opcode(cls) -> int:
        return _CODES.DATA

    @classmethod
    def decode(cls, stream: bytes) -> "TransportDataPacket":
        id = int.from_bytes(stream[:2], ENDIAN)
        length = int.from_bytes(stream[2:4], ENDIAN)
        data = stream[4:]

        packet = cls(id, data)
        packet.length = length

        return packet

    def encode(self) -> bytes:
        return (
            super().encode()
            + self.sequence.to_bytes(2, ENDIAN)
            + self.length.to_bytes(2, ENDIAN)
            + self.data
        )
