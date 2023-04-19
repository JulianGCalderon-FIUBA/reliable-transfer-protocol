from lib.transport.selective_repeat import SelectiveRepeatServerProtocol

transport = SelectiveRepeatServerProtocol(("127.0.0.1", 9000))

while True:
    data, address = transport.recv_from()
    print(f"Llego: {data.decode()} de: {address}")
