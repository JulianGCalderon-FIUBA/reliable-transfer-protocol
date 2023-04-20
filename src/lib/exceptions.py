from lib.packet import Packet


class IncorrectAnswerException(Exception):
    def __init__(self, packet: "Packet"):
        super().__init__()
        self.packet = packet


class FailedHandshake(Exception):
    def __init__(self, reason: str):
        super().__init__()
        self.reason: str = reason

    def __str__(self) -> str:
        return self.reason


class UnorderedPacket(Exception):
    def __init__(self, expected: int, recieved: int):
        super().__init__()
        self.expected = expected
        self.recieved = recieved

    def __str__(self) -> str:
        error_string = \
            f'Expected block number {self.expected} \
                but recieved {self.recieved} instead'
        
        return error_string
    
