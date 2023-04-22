import threading
import socket

from argparse import ArgumentParser
from lib.connection import ConnectionRFTP
from lib.packet import AckFPacket, DataFPacket
from lib.transport.transport import ReliableTransportServer
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
    group.add_argument("-v", "--verbose", action="store_true",
                       help="increase output verbosity")
    group.add_argument("-q", "--quiet", action="store_true",
                       help="decrease output verbosity")

    parser.add_argument(
        "-H", "-host", default="0.0.0.0", type=str, help="service IP address"
    )
    parser.add_argument(
        "-p", "--port", default=9999, type=int, help="service port"
    )  # Puerto donde escucha el servidor
    parser.add_argument("-s", "--storage", default=".",
                        type=str, help="storage dir path")

    return parser


def handle_client(client_sckt):
    while True:
        mensaje, direccion = client_sckt.recvfrom(SERVER_BUFF_SIZE)
        data = DataFPacket.decode(mensaje)
        if not len(data.data):
            break
        print(f"Llego: {DataFPacket.decode(mensaje)} de: {direccion}")
    client_sckt.close()


def main(arguments):
    server = Server(("", 10000), "/home/fran/Documents/distribuidos/")
    server.listen()


if __name__ == "__main__":
    args = start_parser().parse_args()
    main(args)
