from io import BufferedReader
from lib.constants import DATASIZE
from lib.packet import DataFPacket, TransportPacket


class Segmenter:
    def __init__(self):
        self.buffer = None
        self.bytes = bytes()
        self.ended = False

    def segment(self, data: BufferedReader):
        self.buffer = data

    def desegment(self) -> bytes:
        return self.bytes

    def add_segment(self, data: DataFPacket):
        self.bytes += data.data

    def __iter__(self):
        return self

    def __next__(self) -> TransportPacket:
        if self.ended:
            raise StopIteration

        data = self.buffer.read(DATASIZE)  # type: ignore

        if len(data) < DATASIZE:
            self.ended = True

        return DataFPacket(len(data), data)
