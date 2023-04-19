from lib.transport.selective_repeat import SelectiveRepeatClientProtocol

transport = SelectiveRepeatClientProtocol(('127.0.0.1', 9000))

while True:
    line = input("Ingresa una palabra para enviarle al servidor: ")
    transport.send(line.encode())
