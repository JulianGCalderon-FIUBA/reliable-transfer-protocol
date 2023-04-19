from lib.transport.selective_repeat import SelectiveRepeatClientProtocol

transport = SelectiveRepeatClientProtocol(("127.0.0.1", 9000))

sequence = [n for n in range(25)]

for element in sequence:
    transport.send(str(element).encode())
