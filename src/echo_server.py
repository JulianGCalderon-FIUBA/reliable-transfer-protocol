from lib.transport.selective_repeat import SelectiveRepeatServerProtocol
from lib.transport.stop_and_wait import StopAndWaitServerProtocol

ADDRESS = ("127.0.0.1", 9000)

transport = SelectiveRepeatServerProtocol(ADDRESS)
# transport = StopAndWaitServerProtocol(ADDRESS)


while True:
    data, address = transport.recv_from()
    print(f"Llego: {data.decode()} de: {address}")
