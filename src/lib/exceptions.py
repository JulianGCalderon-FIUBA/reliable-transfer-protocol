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


class UnorderedPacket(ErrorPacketException):
    def __init__(self, expected: int = 0, recieved: int = 0):
        super().__init__()
        self.expected = expected
        self.recieved = recieved

    def __str__(self) -> str:
        if self.expected == 0 and self.recieved == 0:
            return "Host recieved an unordered packet"
        error_string = \
            f'Expected block number {self.expected} \
                but recieved {self.recieved} instead'

        return error_string

