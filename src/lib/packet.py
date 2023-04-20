from lib.constants import OPCODES, ENDIAN, END
from abc import ABC, abstractmethod

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
    Devuelve true si la respuesta es la esperada para el paquete.
    Si no devuelve False
    """

    @abstractmethod
    def is_expected_answer(self, other: "Packet") -> bool:
        pass


"""
Devuelve el tipo de paquete (subclase) a partir del opcode

Lanza una excepción si el opcode es invalido
"""


def class_for_opcode(opcode: int) -> type[Packet]:
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

    def is_expected_answer(self, other: "Packet") -> bool:
        if not isinstance(other, AckFPacket):
            return False

        return other.block == 0


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

    def is_expected_answer(self, other: "Packet") -> bool:
        if not isinstance(other, AckFPacket):
            return False

        return other.block == 0


class DataFPacket(Packet):
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
    def decode_as_data(cls, stream: bytes) -> 'DataFPacket':
        packet = Packet.decode(stream)
        if not isinstance(packet, DataFPacket):
            raise Exception("Invalid data packet")
        return packet

    def encode(self) -> bytes:
        return (
            self.opcode.to_bytes(2, ENDIAN)
            + self.block.to_bytes(2, ENDIAN)
            + self.data
        )

    def is_expected_answer(self, other: "Packet") -> bool:
        return isinstance(other, AckFPacket) and other.block == self.block


class AckFPacket(Packet):
    def __init__(self, block_number: int):
        self.opcode: int = OPCODES.ACK
        self.block: int = block_number

    @classmethod
    def decode(cls, stream: bytes) -> "AckFPacket":
        block_number = int.from_bytes(stream, ENDIAN)

        return cls(block_number)

    def encode(self) -> bytes:
        return self.opcode.to_bytes(2, ENDIAN) + self.block.to_bytes(2, ENDIAN)

    def is_expected_answer(self, other: "Packet") -> bool:
        # Esto va a haber que checkearlo, por que el block
        # se puede dar vuelta (volver a 1)
        return isinstance(other, DataFPacket) and other.block == self.block + 1


class ErrorPacket(Packet):
    def __init__(self, error_code: int):
        self.opcode: int = OPCODES.ERROR
        self.error_code: int = error_code

    @classmethod
    def decode(cls, stream: bytes) -> "ErrorPacket":
        error_code = int.from_bytes(stream, ENDIAN)
        return cls(error_code)

    def encode(self) -> bytes:
        return self.opcode.to_bytes(2, ENDIAN) \
                + self.error_code.to_bytes(2, ENDIAN)

    def is_expected_answer(self, other: "Packet") -> bool:
        # Devuelve False, no encontre que tenga un ACK, pero deberia
        # La RFC marca que funciona como ACK para cualquier tipo de paquete.
        return False

    def get_fail_reason(self) -> Exception:
        # Armate un par de error codes.
        return Exception()
