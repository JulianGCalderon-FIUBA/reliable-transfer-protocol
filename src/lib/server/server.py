import random
from threading import Thread, Lock
from lib.connection import ConnectionRFTP
from lib.exceptions import FailedHandshake, FileExists, FilenNotExists
from lib.packet import Packet, ReadRequestPacket, WriteRequestPacket, ErrorPacket, AckFPacket
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
        self.socket = ReliableTransportServer(address)
        self.connections = ConnectionDirectory()
        self.root_directory = root_directory
        self.address = address

    def listen(self) -> None:
        while True:
            packet, address = self.socket.recv_from()
            handshake, from_where = Packet.decode(packet), address        
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
            self.socket.send_to(ErrorPacket.from_exception(FileExists()).encode(), address)
            return
            
        self.attempt_request((self.address[0], get_random_port()),
                             address,
                             file_path)

    def check_read_request(self,
                           request: 'ReadRequestPacket',
                           address: Address):
        file_path = self.build_file_path(request.name)
        if not path.exists(file_path):
            self.socket.send_to(ErrorPacket.from_exception(FilenNotExists()).encode(), address)
            return


        self.attempt_request((self.address[0], get_random_port()),
                             address,
                             file_path,
                             write=False)

    def attempt_request(
            self, worker_address: Address, target_address: Address,
            file_path: str, write=True
            ):
        try:

            if write:
                WriteWorker(target_address, file_path, self.connections).start_thread()
            else:
                ReadWorker(target_address, file_path, self.connections).start_thread()

            return
        except Exception as e:
            print(e)
            self.socket.send_to(ErrorPacket.from_exception(Exception()).encode(), target_address)
            

    def build_file_path(self, filename: str) -> str:
        return self.root_directory + filename


class WriteWorker:

    def __init__(self, target_address: Address,
                 path_to_file: str, connections: ConnectionDirectory) -> None:
        self.dump = open(path_to_file, 'w')
        self.socket = ReliableTransportClient(target_address)
        self.connection = ConnectionRFTP(self.socket)
        self.target = target_address
        self.directory = connections
        self.directory.add_connection(target_address, target_address) # pending

    def start_thread(self):
        Thread(target=self.run).start()

    def run(self):
        self.socket.send_to(AckFPacket(0).encode(), self.target)
        file = self.connection.recieve_file()
        print(f"Writing to file at: {self.dump}")
        self.dump.write(file.decode())
        self.dump.close()
        self.directory.delete_connection(self.target)
        return


class ReadWorker:

    def __init__(self, target_address: Address,
                 path_to_file: str, connections: ConnectionDirectory) -> None:
        
        self.dump = open(path_to_file, 'r').read(-1).encode()
        self.socket = ReliableTransportClient(target_address)
        self.connection = ConnectionRFTP(self.socket) #pending
        self.target = target_address #pending
        self.directory = connections #pending
        self.directory.add_connection(target_address, target_address) # pending #pending
 #pending
    def start_thread(self): #pending
        Thread(target=self.run).start() #pending
 #pending
    def run(self): #pending
        print("Sending!!") #pending
        self.socket.send(AckFPacket(0).encode()) #pending
        print("Handshake sent") #pending
        self.connection.sendto(self.dump, self.target) #pending
        print("Data sent") #pending
        self.directory.delete_connection(self.target) #pending
        return #pending


def get_random_port() -> int:
    return random.randint(30000, 35000)
