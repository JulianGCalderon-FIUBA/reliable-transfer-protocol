from lib.constants import ERRORCODES, OPCODES, ENDIAN, END
from abc import ABC, abstractmethod

from lib.exceptions import (
    FailedHandshake,
    FileExists,
    FilenNotExists,
    InvalidPacket,
)

"""
Define la interfaz para la implementación de cada tipo de paquete
"""


class Packet(ABC):
    """
    Crea cada tipo de paquete particular manualmente
    a partir de los campos especificos
    """

    @abstractmethod
    def __init__():
        pass

    """
    Codifica el paquete en un stream de bytes para ser leido por el receptor
    """

    @abstractmethod
    def encode() -> bytes:
        pass

    """
    Decodifica el paquete a partir de un stream de bytes,
    creando cada instancia particular
    """

    @classmethod
    def decode(cls, stream: bytes) -> "Packet":
        opcode = int.from_bytes(stream[:2], ENDIAN)
        stream = stream[2:]

        return class_for_opcode(opcode).decode(stream)


"""
Devuelve el tipo de paquete (subclase) a partir del opcode

Lanza una excepción si el opcode es invalido
"""


def class_for_opcode(opcode: int) -> type[Packet]:
    if opcode == OPCODES.RRQ:
        return ReadRequestPacket
    if opcode == OPCODES.WRQ:
        return WriteRequestPacket
    if opcode == OPCODES.DATA:
        return DataFPacket
    if opcode == OPCODES.ACK:
        return AckFPacket
    if opcode == OPCODES.ERROR:
        return ErrorPacket

    raise ValueError("invalid opcode")


"""
Lee un campo hasta que llega al byte de terminacion

Devuelve el campo y su longitud
"""


def read_field(stream: bytes) -> tuple[bytes, int]:
    for i in range(0, len(stream)):
        if stream[i] == 0:
            return stream[:i], i

    return stream, len(stream)


class WriteRequestPacket(Packet):
    def __init__(self, name):
        self.opcode: int = OPCODES.WRQ
        self.name: str = name

    @classmethod
    def decode(cls, stream: bytes) -> "WriteRequestPacket":
        name, _length = read_field(stream)
        name = name.decode()
        return cls(name)

    def encode(self) -> bytes:
        return (
            self.opcode.to_bytes(2, ENDIAN)
            + self.name.encode()
            + END.to_bytes(1, ENDIAN)
        )


class ReadRequestPacket(Packet):
    def __init__(self, name):
        self.opcode: int = OPCODES.RRQ
        self.name: str = name

    @classmethod
    def decode(cls, stream: bytes) -> "ReadRequestPacket":
        name, _length = read_field(stream)
        name = name.decode()
        return cls(name)

    def encode(self) -> bytes:
        return (
            self.opcode.to_bytes(2, ENDIAN)
            + self.name.encode()
            + END.to_bytes(1, ENDIAN)
        )


class DataFPacket(Packet):
    def __init__(self, length: int, data: bytes):
        self.opcode: int = OPCODES.DATA
        self.length = length
        self.data: bytes = data

    @classmethod
    def decode(cls, stream: bytes):
        block = int.from_bytes(stream[:2], ENDIAN)
        data = stream[2:]
        return cls(block, data)

    @classmethod
    def decode_as_data(cls, stream: bytes) -> "DataFPacket":
        packet = Packet.decode(stream)
        if not isinstance(packet, DataFPacket):
            raise InvalidPacket()
        return packet

    def encode(self) -> bytes:
        return (
            self.opcode.to_bytes(2, ENDIAN)
            + self.length.to_bytes(2, ENDIAN)
            + self.data
        )


class AckFPacket(Packet):
    def __init__(self):
        self.opcode: int = OPCODES.ACK

    @classmethod
    def decode(cls, _: bytes) -> "AckFPacket":
        return cls()

    def encode(self) -> bytes:
        return self.opcode.to_bytes(2, ENDIAN)


class ErrorPacket(Packet):
    def __init__(self, error_code: int):
        self.opcode: int = OPCODES.ERROR
        self.error_code: int = error_code

    @classmethod
    def decode(cls, stream: bytes) -> "ErrorPacket":
        error_code = int.from_bytes(stream, ENDIAN)
        return cls(error_code)

    def encode(self) -> bytes:
        return self.opcode.to_bytes(2, ENDIAN) + self.error_code.to_bytes(2, ENDIAN)

    @classmethod
    def from_exception(cls, exception: Exception) -> "ErrorPacket":
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
