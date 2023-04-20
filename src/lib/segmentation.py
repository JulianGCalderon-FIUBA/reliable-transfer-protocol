from abc import ABC, abstractmethod
from lib.constants import DATASIZE, MAX_BLOCK_NUMBER

from lib.packet import AckPacket, DataPacket, Packet


class Segmenter:

    def __init__(self, window_size: int):
        self.window_size = window_size
        self.segments = []
        self.window = {}

    
    def segment(self, data: bytes):
        i = 1
        
        while len(data) > 0:
            packet = DataPacket(i % MAX_BLOCK_NUMBER, data[:DATASIZE])
            data = data[DATASIZE:]
            self.segments.append(packet)
            i += 1
        

    def desegment(self) -> bytes:
        self.segments = self.segments + list(self.window.values())
        
        segment_bytes = bytes()
        for segment in self.segments:
            segment_bytes = segment_bytes + segment.data.encode()

        return segment_bytes
    
    def add_segment(self, data: 'Packet'):
        if self.window.get(data.block, None) != None:
            return
        if len(self.window) == self.window_size:
            self.segments = self.segments + list(self.window.values())
            self.window.clear()
        self.window[data.block] = data

    
    def get_next(self) -> 'Packet':
        if len(self.segments) == 0:
            return None
        if len(self.window) < self.window_size:
            self.window[self.segments[0].block] = self.segments[0]
            return self.segments.pop(0)
        #Devolver un error si me pase

    
    def remove_from_ack(self, ack: 'AckPacket'):
        self.window.pop(ack.block)
