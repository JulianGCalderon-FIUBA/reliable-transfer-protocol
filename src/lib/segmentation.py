from lib.constants import DATASIZE
from lib.tftp_packet import TFTPDataPacket


class Segmenter:
    """
    Segments a file into DataFPackets on demand

    This class is lazy. A packet is extracted
    from the file on each iteration.

    Segmentation is done by reading the file in pairs
    to determine if the the end of the file has been reached
    without reading past the end of the file.
    """

    def __init__(self, file_path: str):
        self.file = open(file_path, "rb")

        self.next_packet = self.file.read(DATASIZE)

    def advance_read(self):
        """Advances the read buffers sequence"""
        self.prev_packet = self.next_packet
        self.next_packet = self.file.read(DATASIZE)

    def __iter__(self):
        return self

    def __next__(self) -> TFTPDataPacket:
        """
        Returns the next packet in the file. If the end of the file
        has been reached, returns a packet with the fin flag set to true"""

        self.advance_read()

        if len(self.prev_packet) == 0:
            raise StopIteration

        if len(self.next_packet) == 0:
            return TFTPDataPacket(self.prev_packet, True)

        return TFTPDataPacket(self.prev_packet)


class Desegmenter:
    """
    Constructs a file from DataFPackets"""

    def __init__(self, file_path: str):
        self.file = open(file_path, "wb")

    def add_segment(self, data: bytes):
        """
        Adds a segment to the file"""

        self.file.write(data)

    def close(self):
        """
        Closes the file"""

        self.file.close()
