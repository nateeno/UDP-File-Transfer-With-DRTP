import socket
import argparse
import struct #for DRTP 

# Set up argument parser
parser = argparse.ArgumentParser(description='UDP client and server')
parser.add_argument('--client', '-c', help='Client IP address')
parser.add_argument('--server', '-s', help='Server IP address')
parser.add_argument('--port', '-p', type=int, help='UDP port')
parser.add_argument('--file', '-f', help='File name')
args = parser.parse_args()

UDP_IP = args.server if args.server else "127.0.0.1"
UDP_PORT = args.port if args.port else 8080

# DRTP header fields
sequence_number = 1
acknowledgment_number = 1
flags = 1
file_size = 0

# Create the DRTP header
header = struct.pack('!HHLL', sequence_number, acknowledgment_number, flags, file_size)

"""
Code for the client!
"""

if args.client:
    print('Client started...')
    print("UDP target IP: %s" % UDP_IP)
    print("UDP target port: %s" % UDP_PORT)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
    sock.settimeout(1.0)  # GBN timeout (1sec)


    # Three-way handshake
    sock.sendto(b'SYN', (UDP_IP, UDP_PORT)) # Connection established
    data, addr = sock.recvfrom(1024)
    if data == b'SYN-ACK':
        sock.sendto(b'ACK', (UDP_IP, UDP_PORT)) # Connection established
        
        # Start GBN, after connection 
        sequence_number = 1
        while True:
            try:
                # Create DRTP header and packet
                header = struct.pack('!HHLL', sequence_number, 0, 0, 0) 
                message = 'Hello, Server!'
                packet = header + message.encode() # DRTP Header
                
                # Send packet, wait for ACK
                sock.sendto(packet, (UDP_IP, UDP_PORT))
                data, addr = sock.recvfrom(1024)
                
                # If ACK received, increment sequence number
                if data == b'ACK':
                    sequence_number += 1 # Reliablity function
                    break
            except socket.timeout:
                # If timeout, go back to start of loop to retransmit packet
                continue # Reliablility function 


    """
    Code for the server!
    """

elif args.server:
    print('Server started...')
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP 
    sock.bind((UDP_IP, UDP_PORT))

    expected_sequence_number = 1

    buffer = {} # Buffer to store packets

    while True: 
        data, addr = sock.recvfrom(1024) # buffer size is 1024 bytes
        if data == b'SYN':
            sock.sendto(b'SYN-ACK', addr)
            data, addr = sock.recvfrom(1024)
            if data == b'ACK':
                print('Connection Established (yey)')
                
                # Start (GBN) after connection 
                while True:
                    data, addr = sock.recvfrom(1024)
                    header = data[:12]
                    sequence_number, acknowledgment_number, flags, file_size = struct.unpack('!HHLL', header)
                    message = data[12:].decode()
                    
                    # If received sequence number as expected send ACK + increment expected sequence number
                    if sequence_number == expected_sequence_number:
                        print(f'Received message: {message}, Seq: {sequence_number}, Ack: {acknowledgment_number}, Flags: {flags}, File Size: {file_size}')
                        sock.sendto(b'ACK', addr)
                        expected_sequence_number += 1
                        
                        # Check if the next packet is in the buffer
                        while expected_sequence_number in buffer:
                            data = buffer.pop(expected_sequence_number)
                            header = data[:12]
                            sequence_number, acknowledgment_number, flags, file_size = struct.unpack('!HHLL', header)
                            message = data[12:].decode()
                            print(f'Received message: {message}, Seq: {sequence_number}, Ack: {acknowledgment_number}, Flags: {flags}, File Size: {file_size}')
                            expected_sequence_number += 1
                    elif sequence_number < expected_sequence_number or sequence_number in buffer:
                        # If packet is a duplicate, discard it
                        continue
                    else:
                        # If packet is out of order, store it in buffer
                        buffer[sequence_number] = data


else:
    print('Invalid option. Be cool and use a command bro')