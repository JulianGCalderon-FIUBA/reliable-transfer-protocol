import argparse
import socket

LOCALHOST = "127.0.0.1"
SERVER_BUFF_SIZE = 1024

parser = argparse.ArgumentParser(
    prog="server RFTP",
    description="RFTP server"
)

parser.add_argument("-p", "--port", default=9999, type=int) #Puerto donde escucha el servidor
parser.add_argument("-v", "--verbose") #Si se quiere que el server sea o no verboso


def main(arguments):
    server_sckt = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_sckt.bind((LOCALHOST, arguments.port))

    while True:
        mensaje, direccion = server_sckt.recvfrom(SERVER_BUFF_SIZE)
        print(f"Llego: {mensaje.decode()} de: {direccion}")

if __name__ == "__main__":
    args = parser.parse_args()
    main(args)
