class ErrorPacketException(Exception):
    pass


class FailedHandshake(ErrorPacketException):
    def __init__(self, reason: str = "Failed handshake"):
        super().__init__()
        self.reason: str = reason

    def __str__(self) -> str:
        return self.reason


class FileExists(ErrorPacketException):
    def __str__(self) -> str:
        return "Filename already exists"


class InvalidPacket(ErrorPacketException):
    def __str__(self) -> str:
        return "Recieved an invalid packet"


class FilenNotExists(ErrorPacketException):
    def __str__(self) -> str:
        return "Filename does not exist"
