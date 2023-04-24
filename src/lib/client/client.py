from lib.exceptions import FailedHandshake
from lib.logger import normal_log, verbose_log
from lib.transport.consts import Address
from lib.transport.transport import ReliableTransportClient
from lib.connection import ConnectionRFTP
from lib.packet import (
    AckFPacket,
    ErrorPacket,
    WriteRequestPacket,
    ReadRequestPacket,
    TransportPacket,
)


class Client:
    def __init__(self, address: Address, local_path: str, remote_path: str):
        self.socket = ReliableTransportClient(address)
        self.local_path = local_path
        self.remote_path = remote_path
        self.target_address = address

    def upload(self):
        with open(self.local_path) as upload_file:
            self.send_write_request()
            normal_log(f"Uploading: {self.local_path}")
            data = upload_file.read(-1).encode()

            ConnectionRFTP(self.socket).send_file(data)
            normal_log(
                "Finished upload of file" + f" to server at: {self.target_address}"
            )
            self.socket.close()

    def download(self):
        with open(self.local_path, "bw") as download_file:
            self.send_read_request()
            normal_log(f"Downloading file to: {self.local_path}")
            file_bytes = ConnectionRFTP(self.socket).recieve_file()
            verbose_log(f"Writing to file at: {self.local_path}")
            download_file.write(file_bytes)
            normal_log("Finished downloading file.")
            self.socket.close()

    def send_write_request(self):
        verbose_log(f"Sending upload request to server at: {self.target_address}")
        request = WriteRequestPacket(self.remote_path).encode()
        self.socket.send(request)
        self.expect_answer()

    def send_read_request(self):
        verbose_log(f"Sending download request to server at: {self.target_address}")
        request = ReadRequestPacket(self.remote_path).encode()
        self.socket.send(request)
        self.expect_answer()

    def expect_answer(self):
        answer, address = self.recv_answer()
        answer = TransportPacket.decode(answer)
        verbose_log(
            f"Recovered: {answer.__class__.__name__}" + f" from server at {address}"
        )
        if isinstance(answer, AckFPacket):
            self.socket.set_target(address)
        else:
            self.socket.close()
            if isinstance(answer, ErrorPacket):
                raise answer.get_fail_reason()
            raise FailedHandshake()

    def recv_answer(self):
        while True:
            answer, address = self.socket.recv_from()
            if address[0] == self.target_address[0]:
                return answer, address
