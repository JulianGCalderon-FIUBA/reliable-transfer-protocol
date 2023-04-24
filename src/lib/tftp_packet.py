from enum import IntEnum, auto
from lib.constants import ERRORCODES, ENDIAN, END
from abc import ABC

from lib.exceptions import (
    FailedHandshake,
    FileExists,
    FilenNotExists,
    InvalidPacket,
)


class _CODES(IntEnum):
    RRQ = auto()
    """
    |2 bytes |string   |1 byte |
    |Opcode  |Filename |0      |
    """
    WRQ = auto()
    """
    |2 bytes |string   |1 byte |
    |Opcode  |Filename |0      |
    """
    DATA = auto()
    """
    |2 bytes | 0-512 bytes |
    |Opcode  | Data        |
    """
    ACK = auto()
    """
    |2 bytes |
    |Opcode  |
    """
    ERROR = auto()
    """
    |2 bytes |2 bytes   |
    |Opcode  |ErrorCode |
    """


class TFTPPacket(ABC):
    """
    Base class for all TFTP packets"""

    @classmethod
    def decode(cls, data: bytes) -> "TFTPPacket":
        """
        Decodes a packet from a stream of bytes. Class of the packet
        depends on the opcode"""

        opcode = int.from_bytes(data[:2], ENDIAN)
        data = data[2:]

        for subclass in cls.__subclasses__():
            if subclass._opcode() == opcode:
                return subclass.decode(data)

        raise ValueError("invalid opcode")

    @classmethod
    def _opcode(cls):
        """
        Opcode of the packet"""
        return 0

    def encode(self) -> bytes:
        """
        Encodes the packet to a stream of bytes. The stream of bytes
        starts with the opcode and then the headers specific to each
        subclass. Base implementation only encodes the opcode"""

        return self._opcode().to_bytes(2, ENDIAN)


class TFTPWriteRequestPacket(TFTPPacket):
    def __init__(self, name: str):
        self.name: str = name

    @classmethod
    def decode(cls, stream: bytes) -> "TFTPWriteRequestPacket":
        name, _, stream = stream.partition(END)
        return cls(name.decode())

    @classmethod
    def _opcode(cls) -> int:
        return _CODES.WRQ

    def encode(self) -> bytes:
        return super().encode() + self.name.encode() + END


class TFTPReadRequestPacket(TFTPPacket):
    def __init__(self, name: str):
        self.name: str = name

    @classmethod
    def decode(cls, stream: bytes) -> "TFTPReadRequestPacket":
        name, _, stream = stream.partition(END)
        return cls(name.decode())

    @classmethod
    def _opcode(cls) -> int:
        return _CODES.RRQ

    def encode(self) -> bytes:
        return super().encode() + self.name.encode() + END


class TFTPDataPacket(TFTPPacket):
    def __init__(self, data: bytes):
        self.data: bytes = data

    @classmethod
    def decode(cls, stream: bytes):
        return cls(stream)

    @classmethod
    def _opcode(cls) -> int:
        return _CODES.DATA

    @classmethod
    def decode_as_data(cls, stream: bytes) -> "TFTPDataPacket":
        packet = TFTPPacket.decode(stream)
        if not isinstance(packet, TFTPDataPacket):
            raise InvalidPacket()
        return packet

    def encode(self) -> bytes:
        return super().encode() + self.data


class TFTPAckPacket(TFTPPacket):
    def __init__(self):
        pass

    @classmethod
    def decode(cls, _: bytes) -> "TFTPAckPacket":
        return cls()

    @classmethod
    def _opcode(cls) -> int:
        return _CODES.ACK


class TFTPErrorPacket(TFTPPacket):
    def __init__(self, error_code: int):
        self.error_code: int = error_code

    @classmethod
    def _opcode(cls) -> int:
        return _CODES.ERROR

    @classmethod
    def decode(cls, stream: bytes) -> "TFTPErrorPacket":
        error_code = int.from_bytes(stream[:2], ENDIAN)
        return cls(error_code)

    def encode(self) -> bytes:
        return super().encode() + self.error_code.to_bytes(2, ENDIAN)

    @classmethod
    def from_exception(cls, exception: Exception) -> "TFTPErrorPacket":
        if isinstance(exception, FileExists):
            return cls(ERRORCODES.FILEEXISTS)

        if isinstance(exception, FilenNotExists):
            return cls(ERRORCODES.FILENOTEXISTS)

        if isinstance(exception, FailedHandshake):
            return cls(ERRORCODES.FAILEDHANDSHAKE)

        if isinstance(exception, InvalidPacket):
            return cls(ERRORCODES.INVALIDPACKET)

        return cls(ERRORCODES.UNKNOWN)

    def get_fail_reason(self) -> Exception:
        if self.error_code == ERRORCODES.FILEEXISTS:
            return FileExists()
        if self.error_code == ERRORCODES.FILENOTEXISTS:
            return FilenNotExists()
        if self.error_code == ERRORCODES.FAILEDHANDSHAKE:
            return FailedHandshake()
        if self.error_code == ERRORCODES.INVALIDPACKET:
            return InvalidPacket()

        return Exception("Some unknown error occured")
