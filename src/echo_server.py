import argparse
from lib.transport.selective_repeat import SelectiveRepeatServerProtocol
from lib.transport.stop_and_wait import StopAndWaitServerProtocol

parser = argparse.ArgumentParser(prog="EchoServer")
parser.add_argument("port", type=int)
args = parser.parse_args()

transportSR = SelectiveRepeatServerProtocol(("0.0.0.0", args.port))
transportSNW = StopAndWaitServerProtocol(("0.0.0.0", args.port + 1))

while True:
    data, target = transportSR.recv_from()
    print(f"Llego: {data.decode()} de: {target} en Selective Repeat")

    data, target = transportSNW.recv_from()
    print(f"Llego: {data.decode()} de: {target} en Stop And Wait")
