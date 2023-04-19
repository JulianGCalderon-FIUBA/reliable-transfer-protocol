from lib.transport.selective_repeat import SelectiveRepeatServerProtocol
import atexit

transport = SelectiveRepeatServerProtocol(("127.0.0.1", 9000))
atexit.register(lambda: transport.terminate())

while True:
    data, address = transport.recv_from()
    print(f"Llego: {data.decode()} de: {address}")
