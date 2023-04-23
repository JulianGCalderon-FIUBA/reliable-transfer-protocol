#!/usr/bin/python3

from argparse import ArgumentParser

from lib.server.server import Server

LOCALHOST = "127.0.0.1"
SERVER_BUFF_SIZE = 512


def start_parser() -> "ArgumentParser":
    parser = ArgumentParser(
        prog="server RFTP",
        description="RFTP server",
        usage="start-server [-h] [-v | -q] [-H ADDR] [-p PORT] [-s DIRPATH]",
    )

    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "-v", "--verbose", action="store_true",
        help="increase output verbosity"
    )
    group.add_argument(
        "-q", "--quiet", action="store_true", help="decrease output verbosity"
    )

    parser.add_argument(
        "-H", "--host", default="0.0.0.0", type=str, help="service IP address"
    )
    parser.add_argument(
        "-p", "--port", type=int, help="service port", required=True
    )
    parser.add_argument(
        "-s", "--storage", default="storage/",
        type=str, help="storage dir path"
    )

    return parser


def main(arguments):
    server = Server((arguments.host, arguments.port), arguments.storage)
    while True:
        server.accept()


if __name__ == "__main__":
    args = start_parser().parse_args()
    main(args)
