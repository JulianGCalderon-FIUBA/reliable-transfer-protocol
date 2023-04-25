from abc import ABC
from enum import IntEnum, auto

from lib.transport.exceptions import InvalidPacketException


SEQUENCE_BYTES = 2
LENGTH_BYTES = 2
ENDIAN = "big"


class _CODES(IntEnum):

    """
    Operation codes to distinguish packets."""

    ACK = auto()
    DATA = auto()


class TransportPacket(ABC):
    """
    Base class for all transport packets."""

    @classmethod
    def decode(cls, data: bytes) -> "TransportPacket":
        """
        Decodes a packet from a byte stream. The packet instance will
        depend on the operation code."""

        opcode = int.from_bytes(data[:2], ENDIAN)
        data = data[2:]

        for subclass in cls.__subclasses__():
            if subclass._opcode() == opcode:
                return subclass.decode(data)

        raise InvalidPacketException()

    @classmethod
    def _opcode(cls) -> int:
        """
        Operation code for the packet. Must be implemented by subclasses."""
        return 0

    def encode(self) -> bytes:
        """
        Encodes the packet to a byte stream. The byte stream begins
        with the operation code and then the headers specific to each
        subclass. The base implementation only encodes the operation
        code."""

        return self._opcode().to_bytes(2, ENDIAN)


class TransportAckPacket(TransportPacket):
    """
    Acknowledgement packet for a data packet."""

    def __init__(self, sequence: int):
        """
        The sequence number corresponds to the one from
        the DATA packet being acknowledged."""
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
    Data packet for reliable transport."""

    def __init__(self, sequence: int, data: bytes):
        """
        The sequence number is used to identify the packet and
        to acknowledge it. The data is the payload of the packet."""

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
