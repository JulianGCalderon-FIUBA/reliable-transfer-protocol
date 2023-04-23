import random
from threading import Thread, Lock
from lib.connection import ConnectionRFTP
from lib.exceptions import FailedHandshake, FileExists, FilenNotExists
from lib.packet import Packet, ReadRequestPacket, WriteRequestPacket
from lib.transport.consts import Address
from lib.transport.transport import \
    ReliableTransportClient, ReliableTransportServer
from os import path

random.seed(123)
class ConnectionDirectory:

    def __init__(self):
        self.connections = {}
        self.lock = Lock()

    def lookup(self, address: Address) -> Address:
        self.lock.acquire()
        value = self.connections.get(address, None)
        self.lock.release()
        return value  # type: ignore

    def add_connection(self, address: Address, self_address: Address):
        self.lock.acquire()
        self.connections[address] = self_address
        self.lock.release()

    def delete_connection(self, address: Address):
        self.lock.acquire()
        self.connections.pop(address, None)
        self.lock.release()


class Server:

    def __init__(self, address: Address, root_directory=".") -> None:
        self.connection = ConnectionRFTP(
            ReliableTransportServer(address)
        )
        self.connections = ConnectionDirectory()
        self.root_directory = root_directory
        self.address = address

    def listen(self) -> None:
        print("Listening")
        handshake, from_where = self.connection.listen()

        self.check_request(handshake, from_where)

    def check_request(self, request: 'Packet', address: Address):

        if isinstance(request, ReadRequestPacket):
            return self.check_read_request(request, address)
        elif isinstance(request, WriteRequestPacket):
            return self.check_write_request(request, address)

        raise FailedHandshake()

    def check_write_request(self,
                            request: 'WriteRequestPacket',
                            address: Address):
        print("Attempting an upload")
        file_path = self.build_file_path(request.name)
        if path.exists(file_path):
            self.connection.answer_handshake(address, status=FileExists())
            return
        self.attempt_request((self.address[0], get_random_port()),
                             address,
                             file_path)

    def check_read_request(self,
                           request: 'ReadRequestPacket',
                           address: Address):
        file_path = self.build_file_path(request.name)
        if not path.exists(file_path):
            self.connection.answer_handshake(address, status=FilenNotExists())
            return

        self.attempt_request((self.address[0], get_random_port()),
                             address,
                             file_path,
                             write=False)

    def attempt_request(
            self, worker_address: Address, target_address: Address,
            file_path: str, write=True
            ):

        attempts = 0
        while attempts < 3:
            try:
                worker = WriteWorker(
                    worker_address, target_address, file_path, self.connections
                    ) if write else ReadWorker(
                        worker_address, target_address,
                        file_path, self.connections
                    )
                
                worker.start_thread()
                return
            except Exception as e:
                print(e)
                worker_address = (worker_address[0], get_random_port())
                attempts += 1
        self.connection.answer_handshake(target_address, status=Exception())

    def build_file_path(self, filename: str) -> str:
        return self.root_directory + filename


class WriteWorker:

    def __init__(self, self_address: Address, address: Address,
                 path_to_file: str, connections: ConnectionDirectory) -> None:
        self.dump = open(path_to_file, 'w')
        socket = ReliableTransportServer(self_address)
        self.connection = ConnectionRFTP(
            socket
        )
        self.target = address
        self.directory = connections
        self.directory.add_connection(address, self_address)

    def start_thread(self):
        Thread(target=self.run).start()

    def run(self):
        self.connection.answer_handshake(self.target)
        file = self.connection.recieve_file()
        print(f"Writing to file at: {self.dump}")
        self.dump.write(file.decode())
        self.dump.close()
        self.directory.delete_connection(self.target)
        return


class ReadWorker:

    def __init__(self, self_address: Address, address: Address,
                 path_to_file: str, connections: ConnectionDirectory) -> None:
        
        self.dump = open(path_to_file, 'r').read(-1).encode()
        socket = ReliableTransportServer(self_address)
        self.connection = ConnectionRFTP(
            socket
        )
        self.target = address
        self.directory = connections
        self.directory.add_connection(address, self_address)

    def start_thread(self):
        Thread(target=self.run).start()

    def run(self):
        print("Sending!!")
        self.connection.answer_handshake(self.target)
        print("Handshake sent")
        self.connection.sendto(self.dump, self.target)
        print("Data sent")
        self.directory.delete_connection(self.target)
        return


def get_random_port() -> int:
    return random.randint(30000, 35000)
