from typing import Generator
from lib.constants import DATASIZE
from lib.packet import DataFPacket


class Segmenter:
    def __init__(self, file_path: str):
        self.file_path = file_path

    def segment(self):
        self.file = open(self.file_path, "rb")

    def desegment(self):
        self.file = open(self.file_path, "wb")

    def add_segment(self, data: DataFPacket):
        self.file.write(data.data)

    def __iter__(self) -> Generator[DataFPacket, None, None]:
        while len((data := self.file.read(DATASIZE))) > 0:
            yield DataFPacket(len(data), data)

        self.file.close()
