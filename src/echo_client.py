import argparse
from lib.transport.selective_repeat import SelectiveRepeatClientProtocol
from lib.transport.stop_and_wait import StopAndWaitClientProtocol

parser = argparse.ArgumentParser(prog="EchoClient")
parser.add_argument("ip", type=str)
parser.add_argument("port", type=int)
args = parser.parse_args()

transportSR = SelectiveRepeatClientProtocol((args.ip, args.port))
transportSNW = StopAndWaitClientProtocol((args.ip, args.port + 1))

for element in [str(n) for n in range(25)]:
    print(f"Enviando: {element}")
    transportSR.send(element.encode())
    transportSNW.send(element.encode())
