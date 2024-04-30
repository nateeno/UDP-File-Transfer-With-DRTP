import socket
import argparse

# Set up argument parser
parser = argparse.ArgumentParser(description='UDP client and server')
parser.add_argument('--client', '-c', help='Client IP address')
parser.add_argument('--server', '-s', help='Server IP address')
parser.add_argument('--port', '-p', type=int, help='UDP port')
parser.add_argument('--file', '-f', help='File name')
args = parser.parse_args()

UDP_IP = args.server if args.server else "127.0.0.1"
UDP_PORT = args.port if args.port else 8080

if args.client:
    print('Client started...')
    print("UDP target IP: %s" % UDP_IP)
    print("UDP target port: %s" % UDP_PORT)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP

    # Three-way handshake
    sock.sendto(b'SYN', (UDP_IP, UDP_PORT))
    data, addr = sock.recvfrom(1024)
    if data == b'SYN-ACK':
        sock.sendto(b'ACK', (UDP_IP, UDP_PORT))

elif args.server:
    print('Server started...')
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP 
    sock.bind((UDP_IP, UDP_PORT))

    while True: 
        data, addr = sock.recvfrom(1024) # buffer size is 1024 bytes
        if data == b'SYN':
            sock.sendto(b'SYN-ACK', addr)
            data, addr = sock.recvfrom(1024)
            if data == b'ACK':
                print('Connection Established (yey)')
        else:
            print("received message: %s" % data.decode())
else:
    print('Invalid option. Use -s for server and -c for client.')