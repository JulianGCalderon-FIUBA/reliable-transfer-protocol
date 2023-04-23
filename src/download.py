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
        usage="download [ - h ] [ - v | -q ] [ - H ADDR ] [ - p PORT ] [ - d FILEPATH ] [ - n FILENAME ]"
    )

    group = parser.add_mutually_exclusive_group()
    group.add_argument("-v", "--verbose", help="increase output verbosity")
    group.add_argument("-q", "--quiet", help="decrease output verbosity")

    parser.add_argument("-H", "--host", type=str, help="server IP address", required=True)
    parser.add_argument("-p", "--port", type=int, help="server port", required= True)
    parser.add_argument("-d", "--dst", help="destination file path", required=True)
    parser.add_argument("-n", "--name", help="file name", required=True)

    return parser


def main(arguments):

    socket = ReliableTransportClient((arguments.host, arguments.port))
    connection = ConnectionRFTP(socket)
    file = connection.download(arguments.name,
                               (arguments.host, arguments.port))
    
    print(file.decode())

    socket.close()


if __name__ == "__main__":
    arguments = start_parser().parse_args()
    main(arguments)
