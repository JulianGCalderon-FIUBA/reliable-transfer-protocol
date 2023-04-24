from lib.constants import DATASIZE
from lib.packet import DataFPacket


class Segmenter:
    def __init__(self):
        self.buffer = None
        self.bytes = bytes()

    def segment(self, file_path: str):
        self.buffer = open(file_path, "rb")

    def desegment(self, file_path: str):
        self.buffer = open(file_path, "wb")

    def add_segment(self, data: DataFPacket):
        self.buffer.write(data.data)  # type: ignore

    def close(self):
        self.buffer.close()  # type: ignore

    def __iter__(self):
        return self

    def __next__(self) -> DataFPacket:
        data = self.buffer.read(DATASIZE)  # type: ignore

        if len(data) <= 0:
            self.close()
            raise StopIteration

        return DataFPacket(len(data), data)
