from lib.transport import ClientTransportProtocol


transport = ClientTransportProtocol(('127.0.0.1', 9000))

while True:
    line = input("Ingresa una palabra para enviarle al servidor: ")
    transport.send(line.encode())
