from typing import Self
from constants import OPCODES, ENDIAN
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
    def decode(stream: bytes) -> Self:
        opcode = int.from_bytes(stream[:2], ENDIAN)
        stream = stream[2:]

        class_for_opcode(opcode).decode(stream)



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


class WriteRequestPacket(Packet):
    def __init__(name) -> Self:
        pass

class ReadRequestPacket(Packet):
    def __init__(name) -> Self:
        pass

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
    def __init__(block_number) -> Self:
        pass

class ErrorPacket(Packet):
    def __init__(error_name) -> Self:
        pass

class PacketBuilder():
    pass
