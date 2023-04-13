import argparse
import socket

LOCALHOST = "127.0.0.1"
SERVER_BUFF_SIZE = 1024

parser = argparse.ArgumentParser(
    prog="RFTP client",
    description="Client that allows to upload and download files from a RFTP server"
)

parser.add_argument('-p', '--port', default=8999, type=int) #Default port for RFTP client
parser.add_argument('-sp', '--serverport', default=9999, type=int) #Port where the server is listening
parser.add_argument('-f', '--filepath') #Filepath for sending file
parser.add_argument('-d', '--download' , action='store_true') #If present, then the action is to download a file if not, file will be uploaded
parser.add_argument('-m', '--message', default="Hello, world!")
parser.add_argument('-mc', '--messagecheck', action='store_true') #If present, send message to server instead of file

def main(arguments):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.bind((LOCALHOST, arguments.port))

    client_socket.sendto(arguments.message.encode(), (LOCALHOST, arguments.serverport))
    client_socket.close()

if __name__ == "__main__":
    arguments = parser.parse_args()
    if not arguments.messagecheck:
        print("Not yet implemented")
        exit(-1)
    main(arguments)
    