from lib.transport.selective_repeat import SelectiveRepeatClientProtocol
import atexit

transport = SelectiveRepeatClientProtocol(("127.0.0.1", 9000))
atexit.register(lambda: transport.terminate())

while True:
    line = input("Ingresa una palabra para enviarle al servidor: ")
    transport.send(line.encode())
