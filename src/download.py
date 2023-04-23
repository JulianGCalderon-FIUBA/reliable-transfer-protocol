import argparse
from argparse import ArgumentParser

from lib.connection import ConnectionRFTP
from lib.transport.transport import ReliableTransportClient, ReliableTransportServer

LOCALHOST = "127.0.0.1"
SERVER_BUFF_SIZE = 512


def start_parser() -> "ArgumentParser":
    parser = ArgumentParser(
        prog="Download parser",
        description="Allows to parse download flags received by command line",
    )

    group = parser.add_mutually_exclusive_group()
    group.add_argument("-v", "--verbose", help="increase output verbosity")
    group.add_argument("-q", "--quiet", help="decrease output verbosity")

    parser.add_argument("-H", "--host", type=str, help="server IP address")
    parser.add_argument("-p", "--port", type=int, help="server port")
    parser.add_argument("-d", "--dst", help="destination file path")
    parser.add_argument("-n", "--name", help="file name")

    return parser


def main(arguments):
    if arguments.host is None or arguments.port is None:
        print("no address given")
        return -1

    connection = ReliableTransportServer(("", 10002))
    connection = ConnectionRFTP(connection)
    file = connection.download(arguments.name,
                               (arguments.host, arguments.port))
    print(file.decode())


if __name__ == "__main__":
    arguments = start_parser().parse_args()
    main(arguments)
