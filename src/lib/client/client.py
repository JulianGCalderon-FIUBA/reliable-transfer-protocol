from lib.exceptions import FailedHandshake
from lib.transport.consts import Address
from lib.transport.transport import ReliableTransportClient
from lib.connection import ConnectionRFTP
from lib.packet import AckFPacket, WriteRequestPacket, ReadRequestPacket, Packet


class Client:
    def __init__(self, address: Address, local_path: str, remote_path: str):
        self.socket = ReliableTransportClient(address)
        self.local_path = local_path
        self.remote_path = remote_path
        self.target_address = address

    def upload(self):
        with open(self.local_path) as upload_file:
            self.send_write_request()

            data = upload_file.read(-1).encode()

            ConnectionRFTP(self.socket).send_file(data)

            self.socket.close()

    def download(self):
        with open(self.local_path, "bw") as download_file:
            self.send_read_request()
            file_bytes = ConnectionRFTP(self.socket).recieve_file()

            download_file.write(file_bytes)

            self.socket.close()

    def send_write_request(self):
        request = WriteRequestPacket(self.remote_path).encode()
        self.socket.send(request)
        self.expect_answer()

    def send_read_request(self):
        request = ReadRequestPacket(self.remote_path).encode()
        self.socket.send(request)
        self.expect_answer()

    def expect_answer(self):
        answer, address = self.recv_answer()

        answer = Packet.decode(answer)
        if isinstance(answer, AckFPacket):
            self.socket.set_target(address)
        else:
            raise FailedHandshake()

    def recv_answer(self):
        while True:
            answer, address = self.socket.recv_from()
            if address[0] == self.target_address[0]:
                return answer, address
