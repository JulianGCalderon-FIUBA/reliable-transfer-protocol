#!/usr/bin/python3
from argparse import ArgumentParser
from lib.connection import ConnectionRFTP
from lib.packet import DataFPacket, WriteRequestPacket
from lib.transport.transport import ReliableTransportClient, ReliableTransportServer
from lib.client.client import Client

SERVER_BUFF_SIZE = 512


def start_parser() -> "ArgumentParser":
    parser = ArgumentParser(
        prog="Upload parser",
        description="Allows to parse upload flags received by command line",
        usage=" upload [ - h ] [ - v | -q ] [ - H ADDR ] [ - p PORT ] [ - s FILEPATH ] [ - n FILENAME ]"
    )

    group = parser.add_mutually_exclusive_group()
    group.add_argument("-v", "--verbose", help="increase output verbosity")
    group.add_argument("-q", "--quiet", help="decrease output verbosity")

    parser.add_argument("-H", "--host", type=str, help="server IP address", required=True)
    parser.add_argument("-p", "--port", type=int, help="server port", required=True)
    parser.add_argument("-s", "--src", help="source file path", required=True)
    parser.add_argument("-n", "--name", help="file name", required=True)

    return parser


def main(arguments):
    # send WRQ
    # receive ACK and create Connection with ephemeral target port
    # send file using stop-and-wait
    # receive answer in bound port
    # get host ephemeral port from answer
    address = (arguments.host, arguments.port)
    local_path = arguments.src
    remote_path = arguments.name
    Client(address, local_path, remote_path).upload()

if __name__ == "__main__":
    arguments = start_parser().parse_args()
    main(arguments)
