import argparse

from lib.transport.transport import ReliableTransportClient

parser = argparse.ArgumentParser(prog="EchoClient")
parser.add_argument("ip", type=str)
parser.add_argument("port", type=int)
args = parser.parse_args()

transportSR = ReliableTransportClient((args.ip, args.port))

for element in [str(n) for n in range(25)]:
    print(f"Envio: {element}")
    transportSR.send(element.encode())

for i in range(25):
    data = transportSR.recv()
    print(f"Recibo: {data.decode()}")

transportSR.close()
