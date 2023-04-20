import argparse
from lib.transport.selective_repeat import SelectiveRepeatServerProtocol
from lib.transport.stop_and_wait import StopAndWaitServerProtocol

parser = argparse.ArgumentParser(prog="EchoServer")
parser.add_argument("port", type=int)
args = parser.parse_args()

transportSR = SelectiveRepeatServerProtocol(("0.0.0.0", args.port))
transportSNW = StopAndWaitServerProtocol(("0.0.0.0", args.port + 1))

while True:
    data, address = transportSR.recv_from()
    print(f"Llego: {data.decode()} de: {address} en Selective Repeat")

    data, address = transportSNW.recv_from()
    print(f"Llego: {data.decode()} de: {address} en Stop And Wait")
