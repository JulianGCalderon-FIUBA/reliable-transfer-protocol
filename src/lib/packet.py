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


class TransportPacket(ABC):
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
    def decode(cls, stream: bytes) -> "TransportPacket":
        opcode = int.from_bytes(stream[:2], ENDIAN)
        stream = stream[2:]

        return class_for_opcode(opcode).decode(stream)

    """
    Devuelve true si la respuesta es la esperada para el paquete.
    Si no devuelve False
    """

    @abstractmethod
    def is_expected_answer(self, other: "TransportPacket") -> bool:
        pass


"""
Devuelve el tipo de paquete (subclase) a partir del opcode

Lanza una excepción si el opcode es invalido
"""


def class_for_opcode(opcode: int) -> type[TransportPacket]:
    match opcode:
        case OPCODES.RRQ:
            return ReadRequestPacket
        case OPCODES.WRQ:
            return WriteRequestPacket
        case OPCODES.DATA:
            return DataFPacket
        case OPCODES.ACK:
            return AckFPacket
        case OPCODES.ERROR:
            return ErrorPacket

        case _:
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


class WriteRequestPacket(TransportPacket):
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

    def is_expected_answer(self, other: "TransportPacket") -> bool:
        if not isinstance(other, AckFPacket):
            return False

        return other.block == 0


class ReadRequestPacket(TransportPacket):
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

    def is_expected_answer(self, other: "TransportPacket") -> bool:
        if not isinstance(other, AckFPacket):
            return False

        return other.block == 0


class DataFPacket(TransportPacket):
    def __init__(self, block: int, data: bytes):
        self.opcode: int = OPCODES.DATA
        self.block = block
        self.data: bytes = data

    @classmethod
    def decode(cls, stream: bytes):
        block = int.from_bytes(stream[:2], ENDIAN)
        data = stream[2:]
        return cls(block, data)

    @classmethod
    def decode_as_data(cls, stream: bytes) -> "DataFPacket":
        packet = TransportPacket.decode(stream)
        if not isinstance(packet, DataFPacket):
            raise InvalidPacket()
        return packet

    def encode(self) -> bytes:
        return (
            self.opcode.to_bytes(2, ENDIAN) + self.block.to_bytes(2, ENDIAN) + self.data
        )

    def is_expected_answer(self, other: "TransportPacket") -> bool:
        return isinstance(other, AckFPacket) and other.block == self.block


class AckFPacket(TransportPacket):
    def __init__(self, block_number: int):
        self.opcode: int = OPCODES.ACK
        self.block: int = block_number

    @classmethod
    def decode(cls, stream: bytes) -> "AckFPacket":
        block_number = int.from_bytes(stream, ENDIAN)

        return cls(block_number)

    def encode(self) -> bytes:
        return self.opcode.to_bytes(2, ENDIAN) + self.block.to_bytes(2, ENDIAN)

    def is_expected_answer(self, other: "TransportPacket") -> bool:
        # Esto va a haber que checkearlo, por que el block
        # se puede dar vuelta (volver a 1)
        return isinstance(other, DataFPacket) and other.block == self.block + 1


class ErrorPacket(TransportPacket):
    def __init__(self, error_code: int):
        self.opcode: int = OPCODES.ERROR
        self.error_code: int = error_code

    @classmethod
    def decode(cls, stream: bytes) -> "ErrorPacket":
        error_code = int.from_bytes(stream, ENDIAN)
        return cls(error_code)

    def encode(self) -> bytes:
        return self.opcode.to_bytes(2, ENDIAN) + self.error_code.to_bytes(2, ENDIAN)

    def is_expected_answer(self, other: "TransportPacket") -> bool:
        # Devuelve False, no encontre que tenga un ACK, pero deberia
        # La RFC marca que funciona como ACK para cualquier tipo de paquete.
        return False

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
        match self.error_code:
            case ERRORCODES.FILEEXISTS:
                return FileExists()
            case ERRORCODES.FILENOTEXISTS:
                return FilenNotExists()
            case ERRORCODES.FAILEDHANDSHAKE:
                return FailedHandshake()
            case ERRORCODES.INVALIDPACKET:
                return InvalidPacket()
            case _:
                return Exception("Some unknown error occured")
