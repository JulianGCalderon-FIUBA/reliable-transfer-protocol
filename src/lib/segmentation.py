from lib.constants import DATASIZE


class Segmenter:
    """
    Segments a file into DataFPackets on demand

    This class is lazy. A packet is extracted
    from the file on each iteration
    """

    def __init__(self, file_path: str):
        self.file = open(file_path, "rb")

    def __iter__(self):
        return self

    def __next__(self) -> bytes:
        data = self.file.read(DATASIZE)

        if len(data) <= 0:
            self.file.close()
            raise StopIteration

        return data


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
