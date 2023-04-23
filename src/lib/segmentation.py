from lib.constants import DATASIZE
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

    def desegment(self) -> bytes:
        segment_bytes = bytes()
        for segment in self.segments:
            segment_bytes = segment_bytes + segment.data

        return segment_bytes

    def add_segment(self, data: DataFPacket):
        self.segments.append(data)

    def __iter__(self):
        return self

    def __next__(self) -> Packet:
        if len(self.segments) == 0:
            raise StopIteration

        return self.segments.pop(0)
