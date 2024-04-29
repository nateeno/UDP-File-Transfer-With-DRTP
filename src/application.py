import socket
import sys

UDP_IP = "127.0.0.1"
UDP_PORT = 8080

if len(sys.argv) != 2:
    print('Usage: python application.py -s|-c')
    sys.exit()

if sys.argv[1] == '-c':
    print('Client started...')
    MESSAGE = "Hello World!"

    print("UDP target IP: %s" % UDP_IP)
    print("UDP target port: %s" % UDP_PORT)
    print("Message: %s" % MESSAGE)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
    sock.sendto(MESSAGE.encode(), (UDP_IP, UDP_PORT))

elif sys.argv[1] == '-s':
    print('Server startet...')
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP 
    sock.bind((UDP_IP, UDP_PORT))

    while True: 
        data, addr = sock.recvfrom(1024) # buffer size is 1024 bytes
        print("received message: %s" % data.decode())

else:
    print('Invalid option. Use -s for server and -c for client.')