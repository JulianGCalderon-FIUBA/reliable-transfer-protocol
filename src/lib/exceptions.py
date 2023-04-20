
from lib.packet import Packet


class IncorrectAnswerException(Exception):

    def __init__(self, packet: 'Packet'):
        super().__init__()
        self.packet = packet
