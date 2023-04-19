import argparse
from argparse import ArgumentParser
from lib.connection import StopAndWaitConnection
from lib.packet import DataPacket, WriteRequestPacket

SERVER_BUFF_SIZE = 512

def start_parser() -> 'ArgumentParser':
    parser = argparse.ArgumentParser(
        prog="Upload parser",
        description="Allows to parse upload flags received by command line"
    )

    group = parser.add_mutually_exclusive_group()
    group.add_argument('-v', '--verbose', help = 'increase output verbosity') 
    group.add_argument('-q', '--quiet', help = 'decrease output verbosity') 

    parser.add_argument('-H', '--host', type = str, help = 'server IP address') 
    parser.add_argument('-p', '--port', type = int, help = 'server port') 
    parser.add_argument('-s', '--src', help = 'source file path') 
    parser.add_argument('-n', '--name', help = 'file name', nargs = 1) 

    return parser


def main(arguments):
    # send WRQ
    # receive ACK and create Connection with ephemeral target port
    # send file using stop-and-wait 
    # receive answer in bound port
    # get host ephemeral port from answer
    print(arguments.name)
    connection = StopAndWaitConnection(arguments.host, 9999)
    connection.send_handshake(WriteRequestPacket(arguments.src), (arguments.host, arguments.port))
    with open(arguments.src) as upload_file:
        data = upload_file.read(-1)
        connection.sendto(data, (arguments.host, arguments.port))


if __name__ == "__main__":
    arguments = start_parser().parse_args()
    main(arguments)

