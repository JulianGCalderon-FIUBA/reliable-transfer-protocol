from abc import ABC, abstractmethod
from lib.constants import DATASIZE, MAX_BLOCK_NUMBER

from lib.packet import AckPacket, DataPacket, Packet


class Segmenter:

    def __init__(self, window_size: int):
        self.window_size = window_size
        self.segments = []
        self.window = {}

    
    def segment(self, data: bytes):
        total_data_packets = len(data) // DATASIZE

        for i in range(1, total_data_packets + 1):
            packet = DataPacket(i % MAX_BLOCK_NUMBER, data[:DATASIZE])
            data = data[DATASIZE:]
            self.segments.append(packet)


    
    def add_segment(self, data: 'Packet'):
        if len(self.window) == self.window_size:
            self.segments = self.segments + list(self.window.items())
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

