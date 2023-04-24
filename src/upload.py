#!/usr/bin/python3
from argparse import ArgumentParser
from lib.client.client import Client
import logging

from lib.logger import create_logger, quiet_log

QUIET = logging.WARNING
NORMAL = logging.INFO
VERBOSE = logging.DEBUG


def start_parser() -> "ArgumentParser":
    parser = ArgumentParser(
        prog="Upload parser",
        description="Allows to parse upload flags received by command line",
        usage=" upload [ - h ] [ - v | -q ] [ - H ADDR ] "
        + "[ - p PORT ] [ - s FILEPATH ] [ - n FILENAME ]",
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-v", "--verbose", help="increase output verbosity",
                       default=False, action='store_true')
    group.add_argument("-q", "--quiet", help="decrease output verbosity",
                       default=False, action='store_true')

    parser.add_argument(
        "-H", "--host", type=str, help="server IP address", required=True
    )
    parser.add_argument("-p", "--port", type=int,
                        help="server port", required=True)
    parser.add_argument("-s", "--src", help="source file path", required=True)
    parser.add_argument("-n", "--name", help="file name", required=True)

    return parser


def main(arguments):
    address = (arguments.host, arguments.port)
    local_path = arguments.src
    remote_path = arguments.name
    create_logger(arguments.verbose, arguments.quiet)
    try:
        Client(address, local_path, remote_path).upload()
    except Exception as e:
        quiet_log(">> Error: " + e.__str__())


if __name__ == "__main__":
    arguments = start_parser().parse_args()
    main(arguments)
