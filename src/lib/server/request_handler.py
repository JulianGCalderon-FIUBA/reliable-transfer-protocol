import os
from threading import Thread
from lib.exceptions import FilenNotExists
from lib.packet import (
    TransportPacket,
    ReadRequestPacket,
    WriteRequestPacket,
)
from lib.server.worker import ErrorWorker, ReadWorker, WriteWorker
from lib.transport.consts import Address
from os import path


class Handler:

    def __init__(self, root_directory: str):
        self.root_directory = root_directory

    def handle_request(self, packet: 'TransportPacket', address: Address):
        Thread(target=self.check_request, args=[packet, address]).start()

    def check_request(self, request: TransportPacket, address: Address):
        if isinstance(request, ReadRequestPacket):
            return self.check_read_request(request, address)
        elif isinstance(request, WriteRequestPacket):
            return self.check_write_request(request, address)

        print("Received unknown packet type, ignoring...")

    def check_write_request(self, request: WriteRequestPacket, address: Address):
        absolute_path = self.absolute_path(request.name)
        if path.exists(absolute_path):
            ErrorWorker(address, FileExistsError()).run()
            return
        WriteWorker(address, absolute_path).run()

    def check_read_request(self, request: ReadRequestPacket, address: Address):
        absolute_path = self.absolute_path(request.name)

        if not path.exists(absolute_path):
            ErrorWorker(address, FilenNotExists()).run()
            return

        ReadWorker(address, absolute_path).run()

    def absolute_path(self, relative_path: str) -> str:
        return os.path.join(self.root_directory, relative_path)

