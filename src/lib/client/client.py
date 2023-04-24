from lib.exceptions import FailedHandshake
from lib.logger import normal_log, verbose_log
from lib.transport.consts import Address
from lib.transport.transport import ReliableTransportClient
from lib.connection import ConnectionRFTP
from lib.tftp_packet import (
    TFTPAckPacket,
    TFTPErrorPacket,
    TFTPWriteRequestPacket,
    TFTPReadRequestPacket,
    TFTPPacket,
)


class Client:
    """
    Client interface for the RFTP protocol.

    This class is responsible for downloading and uploading files to the server."""

    def __init__(self, address: Address, local_path: str, remote_path: str):
        self.socket = ReliableTransportClient(address)
        self.local_path = local_path
        self.remote_path = remote_path
        self.target_address = address

    def upload(self):
        """Attempts to upload a file to the server"""

        self._send_write_request()

        normal_log(f"Uploading file: {self.local_path}")
        ConnectionRFTP(self.socket).send_file(self.local_path)
        normal_log("Finished uploading")

        self.socket.close()

    def download(self):
        """Attempts to download a file from the server"""

        self._send_read_request()

        normal_log(f"Downloading file: {self.remote_path}")
        ConnectionRFTP(self.socket).receive_file(self.local_path)
        normal_log("Finished downloading")

        self.socket.close()

    def _send_write_request(self):
        """
        Sends a write request to the server and waits for an answer."""

        verbose_log("Sending upload request to server")
        request = TFTPWriteRequestPacket(self.remote_path).encode()
        self.socket.send(request)

        self._expect_answer()

    def _send_read_request(self):
        """
        Sends a read request to the server and waits for an answer."""

        verbose_log("Sending download request to server")
        request = TFTPReadRequestPacket(self.remote_path).encode()
        self.socket.send(request)

        self._expect_answer()

    def _expect_answer(self):
        """
        Waits for an answer from the server and checks. If it is valid, the
        client will set the target address to the new address of the server.

        If it is invalid,
        an exception is raised."""

        answer, address = self._recv_answer()
        answer = TFTPPacket.decode(answer)
        if isinstance(answer, TFTPAckPacket):
            verbose_log("Received AckFPacket from server")
            self.socket.set_target(address)
            return

        self.socket.close()

        if isinstance(answer, TFTPErrorPacket):
            verbose_log("Received ErrorPacket from server")
            raise answer.get_fail_reason()
        else:
            verbose_log("Received Invalid Packet from server")
            raise FailedHandshake()

    def _recv_answer(self):
        """
        Waits for an answer from the server and returns it."""

        while True:
            answer, address = self.socket.recv_from()
            if address[0] == self.target_address[0]:
                return answer, address
