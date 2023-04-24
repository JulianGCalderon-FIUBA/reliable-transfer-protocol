from lib.constants import DATASIZE
from lib.exceptions import InvalidPacket
from lib.packet import DataFPacket, TransportPacket


class Segmenter:
    def __init__(self):
        self.segments = []
        self.expected_segment = 1

    def segment(self, data: bytes):
        while len(data) > 0:
            packet = DataFPacket(self.expected_segment, data[:DATASIZE])
            data = data[DATASIZE:]
            self.add_segment(packet)

        if len(self.segments[-1].data) == DATASIZE:
            self.segments.append(DataFPacket(self.expected_segment, bytes()))

    def desegment(self) -> bytes:
        segment_bytes = bytes()
        for segment in self.segments:
            segment_bytes = segment_bytes + segment.data

        return segment_bytes

    def add_segment(self, data: DataFPacket):
        if data.block != self.expected_segment:
            raise InvalidPacket()
        self.segments.append(data)
        self.advance_seq_number()

    def advance_seq_number(self):
        self.expected_segment += 1

    def __iter__(self):
        return self

    def __next__(self) -> TransportPacket:
        if len(self.segments) == 0:
            raise StopIteration

        return self.segments.pop(0)
