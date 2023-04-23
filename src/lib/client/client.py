from lib.transport.consts import Address
from lib.transport.transport import ReliableTransportClient
from lib.connection import ConnectionRFTP
from lib.packet import WriteRequestPacket, ReadRequestPacket, Packet

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
            connection = ConnectionRFTP(self.socket)
            connection.send(data)
            self.socket.close()

    def send_write_request(self):
        packet = WriteRequestPacket(self.remote_path)
        print(packet)
        self.socket.send(packet.encode())

        while True:
            answer, address = self.socket.recv_from()
            if address[0] == self.target_address[0]:
                break

        answer = Packet.decode(answer)
        if packet.is_expected_answer(answer):
            self.socket.set_target(address)
        else:
            raise answer.get_fail_reason()  # type: ignore


    def download(self):
        socket = ReliableTransportClient(self.target_address)
        self.send_read_request()
        connection = ConnectionRFTP(socket)
        file = connection.download(arguments.name,
                                (arguments.host, arguments.port))
        
        print(file.decode())

        socket.close()