from abc import ABC, abstractmethod
from enum import IntEnum, auto

ENDIAN = "big"


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
    def __init__(self, id: int):
        self.id = id

    @classmethod
    def opcode(cls) -> int:
        return CODES.ACK

    @classmethod
    def decode(cls, stream: bytes):
        id = int.from_bytes(stream[:2], ENDIAN)

        return cls(id)

    def encode(self) -> bytes:
        return super().encode() + self.id.to_bytes(2, ENDIAN)


class DataPacket(Packet):
    def __init__(self, id: int, data: bytes):
        self.id = id
        self.data = data

    @classmethod
    def opcode(cls) -> int:
        return CODES.DATA

    @classmethod
    def decode(cls, stream: bytes):
        id = int.from_bytes(stream[:2], ENDIAN)
        data = stream[2:]

        return cls(id, data)

    def encode(self) -> bytes:
        return super().encode() + self.id.to_bytes(2, ENDIAN) + self.data
