import threading
import argparse
import socket

from lib.connection import ConnectionRFTP
from lib.packet import AckFPacket, DataFPacket
from lib.transport.selective_repeat import SelectiveRepeatServerProtocol

LOCALHOST = "127.0.0.1"
SERVER_BUFF_SIZE = 512

parser = argparse.ArgumentParser(
    prog="server RFTP",
    description="RFTP server",
    usage="start-server [-h] [-v | -q] [-H ADDR] [-p PORT] [-s DIRPATH]",
)

parser.add_argument(
    "-v", "--verbose", action="store_true", help="increase output verbosity"
)  # Si se quiere que el server sea o no verboso
parser.add_argument(
    "-q", "--quiet", action="store_true", help="decrease output verbosity"
)
parser.add_argument(
    "-H", "-host", default="0.0.0.0", type=str, help="service IP address"
)
parser.add_argument(
    "-p", "--port", default=9999, type=int, help="service port"
)  # Puerto donde escucha el servidor
parser.add_argument("-s", "--storage", default=".", type=str, help="storage dir path")


def handle_client(client_sckt):
    while True:
        mensaje, direccion = client_sckt.recvfrom(SERVER_BUFF_SIZE)
        data = DataFPacket.decode(mensaje)
        if not len(data.data):
            break
        print(f"Llego: {DataFPacket.decode(mensaje)} de: {direccion}")
    sock.close()


def main(arguments):
    connection = SelectiveRepeatServerProtocol(("", 10000))
    connection = ConnectionRFTP(connection)

    handshake, from_where = connection.listen()
    connection.answer_handshake(from_where)

    file = connection.recieve_file()
    print("Termine")
    print(file.decode())


if __name__ == "__main__":
    args = parser.parse_args()
    main(args)
