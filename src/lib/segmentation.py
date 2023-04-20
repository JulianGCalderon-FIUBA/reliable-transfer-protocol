from abc import ABC, abstractmethod
from lib.constants import DATASIZE, MAX_BLOCK_NUMBER

from lib.packet import DataFPacket, Packet


class Segmenter:

    def __init__(self):
        self.segments = []
        self.window = {}

    
    def segment(self, data: bytes):
        i = 1
        
        while len(data) > 0:
            packet = DataFPacket(i % MAX_BLOCK_NUMBER, data[:DATASIZE])
            data = data[DATASIZE:]
            self.segments.append(packet)
            i += 1
            if i % MAX_BLOCK_NUMBER == 0:
                i += 1
        

    def desegment(self) -> bytes:
        self.concatenate_segments()
        
        segment_bytes = bytes()
        for segment in self.segments:
            segment_bytes = segment_bytes + segment.data.encode()

        return segment_bytes
    
    def add_segment(self, data: 'Packet'):
        
        if self.window.get(data.block, None) != None:
            return
        if len(self.window) == MAX_BLOCK_NUMBER:
            self.concatenate_segments()

        self.window[data.block] = data

    def concatenate_segments(self):
        
        for i in range(1, len(self.window) + 1):
            if self.window.get(i, None) == None:
                raise Exception("Falta un bloque")
            self.segments += [self.window.get(i)]

        self.window.clear()
    
    def get_next(self) -> 'Packet':
        if len(self.segments) == 0:
            return None
        return self.segments.pop(0)
        #Devolver un error si me pase


