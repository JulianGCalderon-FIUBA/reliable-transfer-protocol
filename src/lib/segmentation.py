from lib.constants import DATASIZE
from lib.packet import DataFPacket, TransportPacket


class Segmenter:
    def __init__(self):
        self.segments = []

    def segment(self, data: bytes):
        while len(data) > 0:
            packet_data = data[:DATASIZE]
            packet = DataFPacket(len(packet_data), packet_data)
            data = data[DATASIZE:]
            self.add_segment(packet)

        if len(self.segments[-1].data) == DATASIZE:
            self.segments.append(DataFPacket(0, bytes()))

    def desegment(self) -> bytes:
        segment_bytes = bytes()
        for segment in self.segments:
            segment_bytes = segment_bytes + segment.data

        return segment_bytes

    def add_segment(self, data: DataFPacket):
        self.segments.append(data)

    def __iter__(self):
        return self

    def __next__(self) -> TransportPacket:
        if len(self.segments) == 0:
            raise StopIteration

        return self.segments.pop(0)
