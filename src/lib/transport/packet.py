from abc import ABC, abstractmethod
from enum import IntEnum, auto

ENDIAN = "big"

SEQUENCE_BYTES = 2
LENGTH_BYTES = 2

MAX_SEQUENCE = 2 ^ 16 - 1
MAX_LENGTH = 2 ^ 16 - 1


class CODES(IntEnum):
    ACK = auto()
    DATA = auto()


class Packet(ABC):
    @classmethod
    def decode(cls, data: bytes):
        opcode = int.from_bytes(data[:2], ENDIAN)
        data = data[2:]

        for subclass in cls.__subclasses__():
            if subclass.opcode() == opcode:
                return subclass.decode(data)

    @abstractmethod
    def opcode(cls) -> int:
        pass

    def encode(self) -> bytes:
        return self.opcode().to_bytes(2, ENDIAN)


class AckPacket(Packet):
    def __init__(self, sequence: int):
        self.sequence = sequence

    @classmethod
    def opcode(cls) -> int:
        return CODES.ACK

    @classmethod
    def decode(cls, stream: bytes):
        id = int.from_bytes(stream[:2], ENDIAN)

        return cls(id)

    def encode(self) -> bytes:
        return super().encode() + self.sequence.to_bytes(2, ENDIAN)


class DataPacket(Packet):
    def __init__(self, sequence: int, data: bytes):
        self.sequence = sequence
        self.length = len(data)
        self.data = data

    @classmethod
    def opcode(cls) -> int:
        return CODES.DATA

    @classmethod
    def decode(cls, stream: bytes):
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
