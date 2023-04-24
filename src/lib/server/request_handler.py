import os
from threading import Thread
from lib.exceptions import FilenNotExists
from lib.logger import normal_log, verbose_log
from lib.tftp_packet import (
    TFTPPacket,
    TFTPReadRequestPacket,
    TFTPWriteRequestPacket,
)
from lib.server.worker import ErrorWorker, ReadWorker, WriteWorker
from lib.transport.consts import Address
from os import path


class Handler:
    """
    Handler for incoming client requests."""

    def __init__(self, root_directory: str):
        self.root_directory = root_directory

    def handle_request(self, packet: TFTPPacket, address: Address):
        """
        Handles a request from a client in a separate thread"""
        Thread(target=self._handle_request, args=[packet, address]).start()

    def _handle_request(self, request: TFTPPacket, address: Address):
        """
        Handles a request from a client."""

        if isinstance(request, TFTPReadRequestPacket):
            return self._handle_read_request(request, address)
        elif isinstance(request, TFTPWriteRequestPacket):
            return self._handle_write_request(request, address)

        verbose_log("Received unknown packet type, ignoring...")

    def _handle_write_request(self, request: TFTPWriteRequestPacket, address: Address):
        """
        Handles a write request from a client."""

        absolute_path = self._absolute_path(request.name)
        normal_log(f"Recieved upload request from: {address}")

        WriteWorker(address, absolute_path).run()

    def _handle_read_request(self, request: TFTPReadRequestPacket, address: Address):
        """
        Handles a read request from a client."""

        absolute_path = self._absolute_path(request.name)
        normal_log(f"Recieved download request from: {address}")

        if not path.exists(absolute_path):
            ErrorWorker(address, FilenNotExists()).run()
            return

        ReadWorker(address, absolute_path).run()

    def _absolute_path(self, relative_path: str) -> str:
        """
        Returns the absolute path of a file relative to the root directory."""

        return os.path.join(self.root_directory, relative_path)
