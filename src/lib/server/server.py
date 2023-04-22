import random
from threading import Thread, Lock
from lib.connection import ConnectionRFTP
from lib.exceptions import FailedHandshake, FileExists
from lib.packet import Packet, ReadRequestPacket, WriteRequestPacket
from lib.transport.consts import Address
from lib.transport.transport import ReliableTransportClient, ReliableTransportServer
from os import path

class ConnectionDirectory:

    def __init__(self):
        self.connections = {}
        self.lock = Lock()

    def lookup(self, address: Address) -> Address:
        self.lock.acquire()
        value = self.connections.get(address, None)
        self.lock.release()
        return value
    
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
        handshake, from_where = self.connection.listen()
        
        self.check_request(handshake, from_where)


    def check_request(self, request: 'Packet', address: Address):
        
        if isinstance(request, ReadRequestPacket):
            return self.check_read_request(request, address)
        elif isinstance(request,WriteRequestPacket):
            return self.check_write_request(request, address)
        
        raise FailedHandshake()
    
    def check_write_request(self, request: 'WriteRequestPacket', address: Address):
        file_path = self.root_directory + request.name
        print("Entering: ", file_path)
        if path.exists(file_path):
            self.connection.answer_handshake(address, status=FileExists())
            return
        #Aca hay que crear un nuevo socket, desde una nueva direccion y ejecutar lo que esta abajo
        attempts = 0
        while attempts < 3:
            try:
                print("Trying")
                WriteWorker((self.address[0], get_random_port()), address, file_path, self.connections)
                return
            except Exception as e:
                print(e)
                attempts += 1

        self.connection.answer_handshake(address, status=Exception())
        

    def check_read_request(self, request: 'ReadRequestPacket', address: Address):
        pass


class WriteWorker:

    def __init__(self, self_address: Address, address: Address, path_to_file: str, connections: ConnectionDirectory) -> Thread:
        self.dump = open(path_to_file, 'w')
        socket = ReliableTransportClient(address)
        socket.bind(self_address)
        self.connection = ConnectionRFTP(
            socket
        )
        self.target = address
        self.directory = connections
        self.directory.add_connection(address, self_address)
        Thread(target=self.run).run()
    
    def run(self):
        self.connection.answer_handshake(self.target)
        file = self.connection.recieve_file()
        print(f"Writing to file at: {self.dump}")
        self.dump.write(file.decode())
        self.dump.close()
        self.directory.delete_connection(self.target)

    
            

def get_random_port() -> int:
    return random.randint(30000, 35000)
    
