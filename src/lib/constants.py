import types

LOCALHOST = "127.0.0.1"
DEFAULT_STORAGE = "storage/"

ERRORCODES = types.SimpleNamespace()
ERRORCODES.UNORDERED = 1
ERRORCODES.FILEEXISTS = 2
ERRORCODES.FILENOTEXISTS = 3
ERRORCODES.INVALIDPACKET = 4
ERRORCODES.FAILEDHANDSHAKE = 5
ERRORCODES.UNKNOWN = 0

END = b"\0"

ENDIAN = "big"
DATASIZE = 4000
