# TP1 File Transfer

## Server start

In order to start the server, you must run the start_server.py file, which has a help flag to view the different configurations available.

```
$ python3 start_server.py -h
usage: start-server [-h] [-v | -q] [-H ADDR] [-p PORT] [-s DIRPATH]

RFTP server

options:
  -h, --help            show this help message and exit
  -v, --verbose         increase output verbosity
  -q, --quiet           decrease output verbosity
  -H HOST, --host HOST  service IP address
  -p PORT, --port PORT  service port
  -s STORAGE, --storage STORAGE
                        storage dir path                  
```

By default, if the server IP address is not specified, it will run on localhost (this address is configurable through the ```lib/constants.py``` file).

## Upload files
To upload files to the server, you must run upload.py, which supports the following flags:

```
$ python3 upload.py -h
usage:  upload [ -h ] [ -v | -q ] [ -H ADDR ] [ -p PORT ] [ -s FILEPATH ] [ -n FILENAME ]

Allows to parse upload flags received by command line

options:
  -h, --help            show this help message and exit
  -v, --verbose         increase output verbosity
  -q, --quiet           decrease output verbosity
  -H HOST, --host HOST  server IP address
  -p PORT, --port PORT  server port
  -s SRC, --src SRC     source file path
  -n NAME, --name NAME  file name
```
Where "source file path" is the directory where the file to be uploaded is located, and "filename" is the name of the file it will have within the "storage" folder (by default, which is configurable in lib/constants.py).

Example of execution:

```
$ python3 upload.py -s sample_test_file.txt -n test.txt -H 127.0.0.1 -p 7000
>> Uploading file: sample_test_file.txt
>> Finished uploading
```

From the server side:

```
>> Recieving file storage/test.txt from ('127.0.0.1', 35407)
>> File saved at: storage/test.txt
```

## Download files

If one wants to download files from the server, it is necessary to execute download.py, which supports:

```
$ python3 download.py -h
usage: download [ -h ] [ -v | -q ] [ -H ADDR ] [ -p PORT ] [ -d FILEPATH ] [ -n FILENAME ]

Allows to parse download flags received by command line

options:
  -h, --help            show this help message and exit
  -v, --verbose         increase output verbosity
  -q, --quiet           decrease output verbosity
  -H HOST, --host HOST  server IP address
  -p PORT, --port PORT  server port
  -d DST, --dst DST     destination file path
  -n NAME, --name NAME  file name
 ```
 
 Where "destination file path" corresponds to the directory where the file will be stored in the client, and "filename" is the name under which the file is stored in the server.
 
 
 For example, if one wishes to download the previously uploaded test file, the corresponding execution would be as follows:
 
```
$ python3 download.py -H 127.0.0.1 -p 7000 -d test.txt -n test.txt
>> Downloading file: test.txt
>> Finished downloading
```

## Environment variables

All operations (`start_server`, `upload` and `download`) can be executed either using Stop-And-Wait or Selective-Repeat with environment variables.
All of the operations support the environment variable `TFTP_WINDOW_SIZE` which is used to define the amount of UDP packets that can be
waiting for an ACK at any given time.

The default behaviour is Selective-Repeat. To use Stop-And-Wait, set the environment variable to 1 (only 1 packet can be unacked at a time).
Example on how to use Stop-And-Wait for an upload:

```
$ TFTP_WINDOW_SIZE=1 python3 upload.py -H 127.0.0.1 -p 7000 -s test.txt -n test.txt
```

## Logging

Each of the aforementioned files has three logging levels that determine the information displayed during execution. These are:

NORMAL: Executed by default, it displays the execution status (start of download, file sending, file receiving).
QUIET: In this case, only error messages will be displayed during execution, and no other messages. To use the flag -q must be added.
VERBOSE: Increases the level of information displayed from NORMAL mode, including requests, confirmations, among others. To use it, the -v flag must be added.

The three modes can be observed in the following fragments:

NORMAL:

```
$ python3 download.py -H 127.0.0.1 -p 7000 -d test.txt -n test.txt
>> Downloading file: test.txt
>> Finished downloading
```

QUIET:
```
$ python3 download.py -H 127.0.0.1 -p 7000 -d test.txt -n test.txt -q


```

VERBOSE:
```
$ python3 download.py -H 127.0.0.1 -p 7000 -d test.txt -n test.txt -v
>> Sending download request to server
>> Received AckFPacket from server
>> Downloading file: test.txt
>> Finished downloading
```
