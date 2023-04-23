import argparse

from lib.transport.transport import ReliableTransportServer

parser = argparse.ArgumentParser(prog="EchoServer")
parser.add_argument("port", type=int)
args = parser.parse_args()

ANY_ADDRESS = "0.0.0.0"

transportSR = ReliableTransportServer((ANY_ADDRESS, args.port))

for i in range(25):
    data, target = transportSR.recv_from()
    print(f"Recibo: {data.decode()} de: {target}")
    transportSR.send_to(data, target)
