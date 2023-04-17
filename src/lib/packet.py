from typing import Self
from constants import OPCODES, ENDIAN, END
from abc import ABC, abstractmethod

"""
Define la interfaz para la implementación de cada tipo de paquete
"""
class Packet(ABC):
    """
    Crea cada tipo de paquete particular manualmente a partir de los campos especificos
    """
    @abstractmethod
    def __init__() -> Self:
        pass
    
    """
    Codifica el paquete en un stream de bytes para ser leido por el receptor
    """
    @abstractmethod
    def encode() -> bytes:
        pass
    
    """
    Decodifica el paquete a partir de un stream de bytes, creando cada instancia particular
    """
    @classmethod
    def decode(cls, stream: bytes) -> Self:
        opcode = int.from_bytes(stream[:2], ENDIAN)
        stream = stream[2:]

        return class_for_opcode(opcode).decode(stream)



"""
Devuelve el tipo de paquete (subclase) a partir del opcode

Lanza una excepción si el opcode es invalido
"""
def class_for_opcode(opcode: int) -> type:
    match opcode:        
        case OPCODES.RRQ:
            return ReadRequestPacket
        case OPCODES.WRQ:
            return WriteRequestPacket
        case OPCODES.DATA:
            return DataPacket
        case OPCODES.ACK:
            return AckPacket
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
    def __init__(self, name) -> Self:
        self.opcode: int = OPCODES.WRQ
        self.name: str = name

    @classmethod
    def decode(cls, stream: bytes) -> Self:
        name, _length = read_field(stream)
        name = name.decode()
        return cls(name)
    
    def encode(self) -> bytes:
        return (self.opcode.to_bytes(2, ENDIAN) 
                + self.name.encode() 
                + END.to_bytes(1, ENDIAN))

class ReadRequestPacket(Packet):
    def __init__(self, name) -> Self:
        self.opcode: int = OPCODES.RRQ
        self.name: str = name

    @classmethod
    def decode(cls, stream: bytes) -> Self:
        name, _length = read_field(stream)
        name = name.decode()
        return cls(name)
    
    def encode(self) -> bytes:
        return (self.opcode.to_bytes(2, ENDIAN) 
                + self.name.encode() 
                + END.to_bytes(1, ENDIAN))

class DataPacket(Packet):
    def __init__(self, block: int, data: bytes) -> Self:
        self.opcode = OPCODES.DATA
        self.block = block
        self.data = data


    @classmethod
    def decode(cls, stream: bytes):
        block = int.from_bytes(stream[:2], ENDIAN)
        data = stream[2:]
        return cls(block, data)


    def encode(self) -> bytes:
        return (self.opcode.to_bytes(2, ENDIAN)
                + self.block.to_bytes(2, ENDIAN) 
                + self.data)

class AckPacket(Packet):
    def __init__(self, block_number: int) -> Self:
        self.opcode: int = OPCODES.ACK
        self.block: int = block_number
    
    @classmethod
    def decode(cls, stream: bytes) -> Self:
        block_number = int.from_bytes(stream, ENDIAN)

        return cls(block_number)

    def encode(self) -> bytes:
        return (self.opcode.to_bytes(2, ENDIAN)
                + self.block.to_bytes(2, ENDIAN))

class ErrorPacket(Packet):
    def __init__(self, error_code: int) -> Self:
        self.opcode: int = OPCODES.ERROR
        self.error_code: int = error_code

    @classmethod
    def decode(cls, stream: bytes) -> Self:
        error_code = int.from_bytes(stream, ENDIAN)
        return cls(error_code)

    def encode(self) -> bytes:
        return (self.opcode.to_bytes(2, ENDIAN)
                + self.error_code.to_bytes(2, ENDIAN))

class PacketBuilder():
    pass
