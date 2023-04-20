import argparse
from argparse import ArgumentParser
import socket

from lib.connection import StopAndWaitConnection
from lib.packet import ReadRequestPacket

LOCALHOST = "127.0.0.1"
SERVER_BUFF_SIZE = 512


def start_parser() -> "ArgumentParser":
    parser = argparse.ArgumentParser(
        prog="Download parser",
        description="Allows to parse download flags received by command line",
    )

    group = parser.add_mutually_exclusive_group()
    group.add_argument("-v", "--verbose", help="increase output verbosity")
    group.add_argument("-q", "--quiet", help="decrease output verbosity")

    parser.add_argument("-H", "--host", type=int, help="server IP address", nargs=1)
    parser.add_argument("-p", "--port", type=int, help="server port", nargs=1)
    parser.add_argument("-d", "--dst", help="destination file path", nargs=1)
    parser.add_argument("-n", "--name", help="file name", nargs=1)

    return parser


def main(arguments):
    if arguments.host is None or arguments.port is None:
        print("no address given")
        return -1

    server_address = (arguments.host, arguments.port)
    connection = StopAndWaitConnection(server_address)

    request = ReadRequestPacket()
    connection.send(request)

    with open(arguments.name, "w") as file:
        for packet in connection.receive():
            # EXPLOTA SI NO ES UN DATA PACKET !
            file.write(packet.data)


if __name__ == "__main__":
    arguments = start_parser().parse_args()
    main(arguments)
