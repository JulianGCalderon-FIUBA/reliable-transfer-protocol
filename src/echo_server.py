import argparse

from lib.transport.transport import ReliableTransportServer

parser = argparse.ArgumentParser(prog="EchoServer")
parser.add_argument("port", type=int)
args = parser.parse_args()

ANY_ADDRESS = "0.0.0.0"

transportSR = ReliableTransportServer((ANY_ADDRESS, args.port))

while True:
    data, target = transportSR.recv_from()
    print(f"Recibo: {data.decode()} de: {target}")
