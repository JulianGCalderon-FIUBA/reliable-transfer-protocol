from lib.constants import DATASIZE, MAX_BLOCK_NUMBER
from lib.exceptions import UnorderedPacket
from lib.packet import DataFPacket, Packet


class Segmenter:
    def __init__(self):
        self.segments = []
        self.expected_segment = 1

    def segment(self, data: bytes):
        while len(data) > 0:
            packet = DataFPacket(self.expected_segment, data[:DATASIZE])
            data = data[DATASIZE:]
            self.segments.append(packet)
            self.advance_seq_number()

    def desegment(self) -> bytes:
        segment_bytes = bytes()
        for segment in self.segments:
            segment_bytes = segment_bytes + segment.data

        return segment_bytes

    def add_segment(self, data: DataFPacket):
        if self.check_last_segment(data.block):
            self.segments.append(data)
            self.advance_seq_number()
            return
        raise UnorderedPacket(self.expected_segment, data.block)

    def __iter__(self):
        return self

    def __next__(self) -> Packet:
        if len(self.segments) == 0:
            raise StopIteration

        return self.segments.pop(0)

    def check_last_segment(self, new_segment: int) -> bool:
        return self.expected_segment == new_segment

    def advance_seq_number(self):
        if self.expected_segment == MAX_BLOCK_NUMBER:
            self.expected_segment = 0
        self.expected_segment += 1
