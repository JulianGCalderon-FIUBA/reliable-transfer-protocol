from lib.transport.selective_repeat import SelectiveRepeatClientProtocol

ADDRESS = ("127.0.0.1", 9000)

transport = SelectiveRepeatClientProtocol(ADDRESS)

for element in [str(n) for n in range(25)]:
    print(f"Enviando: {element} a: {ADDRESS}")
    transport.send(element.encode())
