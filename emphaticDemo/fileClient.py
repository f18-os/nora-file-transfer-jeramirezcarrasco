#! /usr/bin/env python3

# Echo client program
import time
import socket, sys, re, os
sys.path.append("../lib")       # for params
import params

switchesVarDefaults = (
    (('-s', '--server'), 'server', "127.0.0.1:50001"),
    (('-?', '--usage'), "usage", False), # boolean (set if present)
    )

progname = "fileClient"
paramMap = params.parseParams(switchesVarDefaults)

server, usage  = paramMap["server"], paramMap["usage"]

if usage:
    params.usage()

try:
    serverHost, serverPort = re.split(":", server)
    serverPort = int(serverPort)
except:
    print("Can't parse server:port from '%s'" % server)
    sys.exit(1)

s = None
for res in socket.getaddrinfo(serverHost, serverPort, socket.AF_UNSPEC, socket.SOCK_STREAM):
    af, socktype, proto, canonname, sa = res
    try:
        print("creating sock: af=%d, type=%d, proto=%d" % (af, socktype, proto))
        s = socket.socket(af, socktype, proto)
    except socket.error as msg:
        print(" error: %s" % msg)
        s = None
        continue
    try:
        print(" attempting to connect to %s" % repr(sa))
        s.connect(sa)
    except socket.error as msg:
        print(" error: %s" % msg)
        s.close()
        s = None
        continue
    break

if s is None:
    print('could not open socket')
    sys.exit(1)

#////////////////////////////////////////////////////////////////////////////////////

# Lets start with a simple telling the server which file is going to be send

while(1):
    file = input("Which file are you going to upload\n")
    if os.path.exists(file):
        pass
    else:
        print("File not found\n")
        continue
    lengths = len(file) + len(str((len(file)))) + 1
    outMessage = str(lengths) + " " + file  # This is to make s
    s.send(outMessage.encode())
    ServerReady = s.recv(100).decode()
    if ServerReady == "X":
        print("File is already in the server")
        continue
    elif ServerReady == "O":
        pass
    OpenFile = open(file, "r")
    FilePacket = OpenFile.read(96)  # the 96 is to leave space for the header which will never go beyond 4 bytes
    while FilePacket:  # Here we start iterating through the file
        lengths = len(FilePacket) + len(str((len(FilePacket)))) + 1
        FilePacket = str(lengths) + " " + FilePacket  # Adding the size of the file into the header
        s.send(FilePacket.encode())
        try:
            s.settimeout(10)  # If the server does not answer after 5 second server is not responding
            Recv = s.recv(100).decode()
            while Recv != "R":  # This will tell the client if the server got the entire message or an exception
                if Recv == "M":  # Telling the Client that there was a timeout meaning that part of the file was lost
                    s.send(FilePacket.encode())  # We start the entire message again assuming the server discards the missing pacakge
                    try:
                        s.settimeout(10)
                        Recv = s.recv(100).decode()
                        continue
                    except s.timeout:
                        print("Timeout : Server is not responding")
                        sys.exit()
        except s.timeout:
            print("Timeout : Server is not responding")
            sys.exit()
        print("....")
        FilePacket = OpenFile.read(96)  # If we reach this point it means the server got the entire message and we send the next part
    s.send("-1".encode())  # This will tell the server that the transfer is finished






