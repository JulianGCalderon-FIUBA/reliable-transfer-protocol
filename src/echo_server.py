from lib.transport.selective_repeat import SelectiveRepeatServerProtocol

ADDRESS = ("127.0.0.1", 9000)

transport = SelectiveRepeatServerProtocol(ADDRESS)

while True:
    data, address = transport.recv_from()
    print(f"Llego: {data.decode()} de: {address}")
