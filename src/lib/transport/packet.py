from abc import ABC, abstractmethod
from enum import IntEnum, auto

from lib.transport.consts import ENDIAN


class CODES(IntEnum):
    """
    Codigos de operacion para los paquetes."""

    ACK = auto()
    DATA = auto()


class Packet(ABC):
    """
    Clase base para los paquetes."""

    @classmethod
    def decode(cls, data: bytes) -> "Packet":
        """
        Decodifica un paquete a partir de un stream de bytes.
        La instancia del paquete dependera del codigo de operacion."""

        opcode = int.from_bytes(data[:2], ENDIAN)
        data = data[2:]

        for subclass in cls.__subclasses__():
            if subclass.opcode() == opcode:  # type: ignore
                return subclass.decode(data)

        raise ValueError(f"Invalid opcode: {opcode}")

    @abstractmethod
    def opcode(cls) -> int:
        """
        Codigo de operacion del paquete."""
        pass

    def encode(self) -> bytes:
        """
        Codifica el paquete a un stream de bytes.
        El stream de bytes comienza con el codigo de operacion
        y luego los datos del paquete.
        El codigo de operacion ya es codificado por la implementacion base."""
        return self.opcode().to_bytes(2, ENDIAN)


class AckPacket(Packet):
    """
    Paquete de acknowledgment del paquete DATA."""

    def __init__(self, sequence: int):
        """
        Se define con un numero de secuencia.
        Corresponde al numero de secuencia del paquete DATA"""
        self.sequence = sequence

    @classmethod
    def opcode(cls) -> int:
        return CODES.ACK

    @classmethod
    def decode(cls, stream: bytes) -> "AckPacket":
        id = int.from_bytes(stream[:2], ENDIAN)

        return cls(id)

    def encode(self) -> bytes:
        return super().encode() + self.sequence.to_bytes(2, ENDIAN)


class DataPacket(Packet):
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
    def opcode(cls) -> int:
        return CODES.DATA

    @classmethod
    def decode(cls, stream: bytes) -> "DataPacket":
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
