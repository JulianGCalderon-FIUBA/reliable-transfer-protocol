from lib.transport import ServerTransportProtocol


transport = ServerTransportProtocol(('127.0.0.1', 9000))

while True:
    data, address = transport.receive()
    print(f"Llego: {data.decode()} de: {address}")
