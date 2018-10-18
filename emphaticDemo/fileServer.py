#! /usr/bin/env python3
import sys, os, socket, params, time
from threading import Thread
from framedSock import FramedStreamSock

switchesVarDefaults = (
    (('-l', '--listenPort') ,'listenPort', 50001),
    (('-d', '--debug'), "debug", False), # boolean (set if present)
    (('-?', '--usage'), "usage", False), # boolean (set if present)
    )

progname = "echoserver"
paramMap = params.parseParams(switchesVarDefaults)

debug, listenPort = paramMap['debug'], paramMap['listenPort']

if paramMap['usage']:
    params.usage()

lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # listener socket
bindAddr = ("127.0.0.1", listenPort)
lsock.bind(bindAddr)
lsock.listen(5)
print("listening on:", bindAddr)
print("Ready to connect")

class ServerThread(Thread):
    requestCount = 0            # one instance / class

    def __init__(self, sock, debug):
        Thread.__init__(self, daemon=True)
        self.fsock, self.debug = sock, debug
        self.start()

    def run(self):
        while 1:
            print("new child process handling connection from", addr)
            print("waiting for filename\n")
            filename = self.fsock.recv(100).decode()
            if filename:  # this will be use to make sure that at least the length of the file is receive
                if len(filename.split()) < 2:
                    filename = filename + self.fsock.recv(100).decode()
                MessageLength = int(filename.split()[0])
                while len(filename) < MessageLength:
                    filename = filename + self.fsock.recv(
                        1024).decode()  # This is use to make sure the entire message is receive
                filename = "new" +filename[
                           len(str(filename.split()[0])) + 1:]  # This is to remove the header from the file name
                if os.path.exists(filename):
                    self.fsock.send("X".encode())  # keeping the handshake simple, an X if file found and a O if file not stored
                    continue
                else:
                    self.fsock.send("O".encode())  # Server is ready to receive
                print("File name receive staring download ")
                print(filename)
                IncomingFile = open(filename, "w")
                IncomingPacket = self.fsock.recv(100).decode()
                MessageLength = int(IncomingPacket.split()[0])

                while IncomingPacket != "-1":  # if -1 is receive it means the file is over
                    try:
                        while len(IncomingPacket) != MessageLength or len(IncomingPacket) < MessageLength:
                            IncomingPacket = IncomingPacket + self.fsock.recv(
                                100).decode()  # This will check the message is send compelatly
                        IncomingPacket = IncomingPacket[len((IncomingPacket.split()[0])):]
                        IncomingFile.write(IncomingPacket)
                        self.fsock.send("R".encode())  # Send R if the message was receive
                        IncomingPacket = self.fsock.recv(100).decode()
                        if IncomingPacket.split()[0] == "-":
                            break
                        MessageLength = int(IncomingPacket.split()[0])

                    except self.fsock.timeout:
                        self.fsock.send("M".encode())  # Send M if there was a error
                        IncomingPacket = self.fsock.recv(100).decode()  # Start the process again

                IncomingFile.close()
                print("Download Completed")

#First we are gonna wait for the file name

while True:
    sock, addr = lsock.accept()
    ServerThread(sock, debug)