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
Function for the server
"""
def write_chunks_to_file(file_chunks):
    # Write the file chunks to a new file
    with open('img/received_file.jpg', 'wb') as file:
        for chunk in file_chunks:
            file.write(chunk)


"""
Code for the client!
"""

if args.client:
    print('Client started...')
    print("UDP target IP: %s" % UDP_IP)
    print("UDP target port: %s" % UDP_PORT)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
    sock.settimeout(1.0)  # GBN timeout (1sec)

    # FOR JPG:
    # Open the file in binary mode and read its contents
    with open(args.file, 'rb') as file:
        file_data = file.read()
    
    # Split the file data into chunks 
    MAX_PACKET_SIZE = 1024
    file_chunks = [file_data[i:i+MAX_PACKET_SIZE] for i in range(0, len(file_data), MAX_PACKET_SIZE)]


    # Three-way handshake
    sock.sendto(b'SYN', (UDP_IP, UDP_PORT))
    data, addr = sock.recvfrom(4096)
    if data == b'SYN-ACK':
        sock.sendto(b'ACK', (UDP_IP, UDP_PORT))
        
        # Start GBN, after connection 
        sequence_number = 1
        for chunk in file_chunks:
            try:
                # Create DRTP header and packet
                flags = 1 if file_chunks.index(chunk) == len(file_chunks) - 1 else 0  # set flag to 1 if this is the last chunk
                header = struct.pack('!HHLL', sequence_number, 0, flags, 0)
                packet = header + chunk
                
                # Send packet and wait for ACK
                sock.sendto(packet, (UDP_IP, UDP_PORT))
                data, addr = sock.recvfrom(4096)
                
                # If ACK received, increment sequence number
                if data == b'ACK':
                    sequence_number += 1
            except socket.timeout:
                # If timeout, go back to start of loop to retransmit packet
                continue


    """
    Code for the server!
    """

elif args.server:
    print('Server started...')
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP 
    sock.bind((UDP_IP, UDP_PORT))

    expected_sequence_number = 1

    buffer = {}  # Buffer to store packets
    file_chunks = []  # Buffer to store file chunks

    file_transfer_complete = False  

    while True: 
        data, addr = sock.recvfrom(4096)  # buffer size is 4096 bytes
        if data == b'SYN':
            sock.sendto(b'SYN-ACK', addr)
            data, addr = sock.recvfrom(4096)
            if data == b'ACK':
                print('Connection Established (yey)')

                # Start receiving file chunks
                while True:
                    data, addr = sock.recvfrom(4096)
                    header = data[:12]
                    sequence_number, acknowledgment_number, flags, file_size = struct.unpack('!HHLL', header)
                    chunk = data[12:]

                    if sequence_number == expected_sequence_number:
                        file_chunks.append(chunk)  # Add the chunk to the list
                        sock.sendto(b'ACK', addr)
                        expected_sequence_number += 1

                        # If this was the last packet, break the loop
                        if flags == 1:
                            file_transfer_complete = True  
                            break

                        # Check if the next packet is in the buffer
                        while expected_sequence_number in buffer:
                            data = buffer.pop(expected_sequence_number)
                            header = data[:12]
                            sequence_number, acknowledgment_number, flags, file_size = struct.unpack('!HHLL', header)
                            chunk = data[12:]
                            file_chunks.append(chunk)  # Add the chunk to the list
                            expected_sequence_number += 1
                    elif sequence_number < expected_sequence_number or sequence_number in buffer:
                        # If packet is a duplicate, discard it
                        continue
                    else:
                        # If packet is out of order, store it in buffer
                        buffer[sequence_number] = data

        if file_transfer_complete:  
            break  

    # Call the function to write chunks to file after the while loop
    write_chunks_to_file(file_chunks)

else:
    print('Invalid option. Be cool and use a command bro')