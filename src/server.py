import socket

UDP_IP = "127.0.0.1"
UDP_PORT = 8080

socket = socket.socket(socket.AF_INET, #Internet
                       socket.SOCK_DGRAM) # UDP 
socket.bind((UDP_IP,UDP_PORT))

while True: 
    data, addr = socket.recvfrom(1024) # buffer size is 1024 bytes
    print("recived message: %s" % data)