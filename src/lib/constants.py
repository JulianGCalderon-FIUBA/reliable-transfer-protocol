import types

LOCALHOST = "127.0.0.1"
WILDCARD_ADDRESS = "0.0.0.0"

OPCODES = types.SimpleNamespace()
SOCK_CONSTS = types.SimpleNamespace()
ERRORCODES = types.SimpleNamespace()

"""
    |2 bytes |string   |1 byte |
    |Opcode  |Filename |0      |
"""
OPCODES.RRQ = 1
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

ERRORCODES.UNORDERED = 1
ERRORCODES.FILEEXISTS = 2
ERRORCODES.FILENOTEXISTS = 3
ERRORCODES.INVALIDPACKET = 4
ERRORCODES.FAILEDHANDSHAKE = 5


END = 0x0
MIN_HOST_AMOUNT = 2
LINK_LOSS = 10
ENDIAN = "big"
DATASIZE = 512
BUFFSIZE = 600
MAX_BLOCK_NUMBER = 0xFF

SOCK_CONSTS.BUFFSIZE = 600  # Esto habria que mirarlo mejor despues
SOCK_CONSTS.BASE_TIMEOUT = 1.0  # Un segundo de timeout de base
SOCK_CONSTS.MAX_HANDSHAKE_RETRIES = 3  # Tratamos hasta 3 veces de rehacer una conexion
