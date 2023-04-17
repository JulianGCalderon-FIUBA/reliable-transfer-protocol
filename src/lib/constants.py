import types

LOCALHOST = "127.0.0.1"
WILDCARD_ADDRESS = "0.0.0.0"

OPCODES = types.SimpleNamespace()

"""
    |2 bytes |string   |1 byte |
    |Opcode  |Filename |0      |
"""
OPCODES.RQQ = 1
OPCODES.WRQ = 2

"""
    |2 bytes |2 bytes |0-512 bytes |
    |Opcode  |Block # |Data        |

    Todos tienen 512 bytes, menos el ultimo que tiene menos
"""
OPCODES.DATA = 3

"""
    |2 bytes |2 bytes |
    |Opcode  |Block # |
"""
OPCODES.ACK = 4

"""
    |2 bytes |2 bytes   |string |end byte|
    |Opcode  |ErrorCode |ErrMsg |0       |
"""
OPCODES.ERROR = 5

END = 0x0
MIN_HOST_AMOUNT = 2
LINK_LOSS = 10
ENDIAN = 'big'

BUFFSIZE = 600 #Esto habria que mirarlo mejor despues
