import socket
import argparse
import struct  # for DRTP
import time

# Initialize argument parser
parser = argparse.ArgumentParser(description='UDP client and server')
parser.add_argument('--client', '-c', action='store_true', help='Run as client')
parser.add_argument('--server', '-s', action='store_true', help='Run as server')
parser.add_argument('--ip', '-i', help='IP address of the server')
parser.add_argument('--port', '-p', type=int, help='UDP port')
parser.add_argument('--file', '-f', type=str, help='File name')
parser.add_argument('--window', '-w', type=int, default=3, help='Sliding window size')
parser.add_argument('--discard', '-d', type=int, help='Seq number to discard for retransmission test')
args = parser.parse_args()

# Parse command-line arguments
UDP_IP = args.ip or "127.0.0.1"
UDP_PORT = args.port or 8080
WINDOW_SIZE = args.window
DISCARD_SEQ = args.discard

# Validate port number
if not (1024 <= UDP_PORT <= 65535):
    print("Error: Port number must be in the range 1024-65535")
    exit(1)

# Define DRTP header fields
header_format = '!HHH'  # sequence number, acknowledgment number, and flags are all 2 bytes
sequence_number = 2
acknowledgment_number = 2
flags = 2
file_size = 0

BUFFER_SIZE = 4096
MAX_PACKET_SIZE = 1000

# Construct DRTP header
header = struct.pack(header_format, sequence_number, acknowledgment_number, flags)

"""
Function to write chunks of file
"""
def write_chunks_to_file(file_chunks):
    try:
        with open('img/received_file.jpg', 'wb') as file:
            for chunk in file_chunks:
                file.write(chunk)
    except Exception as e:
        print(f"Error writing to file: {e}")
        exit(1)

"""
Function for the server
"""
def write_chunks_to_file(file_chunks):
    try:
        with open('img/received_file.jpg', 'wb') as file:
            for chunk in file_chunks:
                file.write(chunk)
    except Exception as e:
        print(f"Error writing to file: {e}")
        exit(1)

"""
Code for the client
"""

if args.client:
    try:
        print('Client started...')
        print("UDP target IP: %s" % UDP_IP)
        print("UDP target port: %s" % UDP_PORT)
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
        sock.settimeout(1.0)  # GBN timeout (1sec)

        # Open the file in binary mode and read its contents
        try:
            with open(args.file, 'rb') as file:
                file_data = file.read()
        except FileNotFoundError:
            print(f"File {args.file} not found. Please check the file path and try again.")
            exit(1)
        except Exception as e:
            print(f"An error occurred while opening the file: {e}")
            exit(1)

        # Define the size of the DRTP header
        header_size = struct.calcsize(header_format)

        # Calculate the size of the data chunk
        chunk_size = MAX_PACKET_SIZE - header_size

        # Split the file data into chunks 
        file_chunks = [file_data[i:i+chunk_size] for i in range(0, len(file_data), chunk_size)]

        # Print the number of chunks (packets to be sent)
        print(f'Number of packets: {len(file_chunks)}')

        # Three-way handshake
        sock.sendto(b'SYN', (UDP_IP, UDP_PORT))
        data, addr = sock.recvfrom(BUFFER_SIZE)
        if data == b'SYN-ACK':
            print("SYN-ACK packet is received")
            sock.sendto(b'ACK', (UDP_IP, UDP_PORT))
            print("ACK packet is sent")
            print("Connection established")

            # Start time
            start_time = time.time()

            # Start GBN, after connection 
            sequence_number = 1

            # Sliding window implementation
            base = 1
            nextseqnum = 1
            window_size = WINDOW_SIZE
            frame_buffer = [None] * window_size

            window_packets = []
            while base <= len(file_chunks):
                while nextseqnum < base + window_size and nextseqnum <= len(file_chunks):
                    # Create DRTP header and packet
                    flags = 1 if nextseqnum == len(file_chunks) else 0  # set flag to 1 if this is the last chunk
                    header = struct.pack(header_format, nextseqnum, 0, flags)
                    packet = header + file_chunks[nextseqnum - 1]
                    
                    # Store the packet in the frame buffer
                    frame_buffer[(nextseqnum - 1) % window_size] = packet

                    # Add sequence number to the window
                    window_packets.append(nextseqnum)

                    # Send packet and wait for ACK
                    sock.sendto(packet, (UDP_IP, UDP_PORT))
                    print(f"{time.strftime('%H:%M:%S')} -- packet with seq = {nextseqnum} is sent, sliding window = {window_packets}")

                    nextseqnum += 1

                try:
                    data, addr = sock.recvfrom(BUFFER_SIZE)

                    # Unpack the received data into an integer
                    ack = struct.unpack('!H', data)[0]

                    if ack >= base and ack < nextseqnum:
                        # Remove acknowledged packets from the window
                        window_packets = [seq for seq in window_packets if seq > ack]

                        base = ack + 1
                except socket.timeout:
                    # If timeout, retransmit all unacknowledged frames
                    print(f"Timeout, retransmitting unacknowledged packets")
                    for i in range(base, nextseqnum):
                        sock.sendto(frame_buffer[(i - 1) % window_size], (UDP_IP, UDP_PORT))
                        print(f"{time.strftime('%H:%M:%S')} -- packet with seq = {i} is resent, sliding window = {window_packets}")

            # After sending all packets
            sock.sendto(b'FIN', (UDP_IP, UDP_PORT))
            print(f"{time.strftime('%H:%M:%S')} -- FIN packet is sent")
            data, addr = sock.recvfrom(4096)
            if data == b'ACK':
                print("ACK packet is received")
                print("Connection terminated")
                sock.close()  # Close the socket
            
            # End time
            end_time = time.time()

            # Calculate elapsed time and throughput:
            elapsed_time = end_time - start_time
            file_size_bits = len(file_data) * 8
            throughput = file_size_bits / elapsed_time
            throughput_mbps = throughput / 1000000
            print(f"The throughput is {throughput_mbps} Mbps")

            pass
    except Exception as e:
        print(f"An error occurred: {e}")


    """
    Code for the server!
    """

elif args.server:
    try:
        print('Server started...')
        
        start_time = time.time()
        data_received = False

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP 
            sock.bind((UDP_IP, UDP_PORT))
        except socket.error as e:
            print(f"Error creating/binding socket: {e}")
            exit(1)

        expected_sequence_number = 1

        buffer = {}  # Buffer to store packets
        file_chunks = []  # Buffer to store file chunks

        file_transfer_complete = False  

         # Define the size of the DRTP header
        header_size = struct.calcsize(header_format)

        while True: 
            try:
                data, addr = sock.recvfrom(4096)  # buffer size is 4096 bytes
                if data == b'SYN':
                    print("SYN packet is received")
                    sock.sendto(b'SYN-ACK', addr)
                    print("SYN-ACK packet is sent")

                    data, addr = sock.recvfrom(4096)
                    if data == b'ACK':
                        print('Connection Established (yey)')

                        start_time = time.time()
                        data_received = True

                        # Start receiving file chunks
                        while True:
                            data, addr = sock.recvfrom(4096)
                            header = data[:header_size]  
                            sequence_number, acknowledgment_number, flags = struct.unpack(header_format, header)  
                            chunk = data[header_size:]  

                            # If sequence_number is what we expected, send an ACK back
                            if sequence_number == expected_sequence_number:
                                print(f"{time.strftime('%H:%M:%S')} -- packet {sequence_number} is received")

                                file_chunks.append(chunk)  # Add the chunk to the list
                                ack = struct.pack('!H', sequence_number)  # pack sequence number into binary
                                sock.sendto(ack, addr)  # send acknowledgement
                                print(f"sending ack for the received {sequence_number}")

                                expected_sequence_number += 1

                                # If this was the last packet, break the loop
                                if flags == 1:
                                    file_transfer_complete = True  
                                    break

                                # Check if the next packet is in the buffer
                                while expected_sequence_number in buffer:
                                    data = buffer.pop(expected_sequence_number)
                                    header = data[:6]
                                    sequence_number, acknowledgment_number, flags = struct.unpack(header_format, header)
                                    chunk = data[6:]
                                    file_chunks.append(chunk)  # Add the chunk to the list
                                    expected_sequence_number += 1
                            elif sequence_number < expected_sequence_number or sequence_number in buffer:
                                # If packet is a duplicate, discard it
                                continue
                            else:
                                # If packet is out of order, store it in buffer
                                buffer[sequence_number] = data

                if file_transfer_complete:
                    print(f'Total number of packets received: {sequence_number}')
                    break  

            except KeyboardInterrupt:
                print("\nServer interrupted by user. Shutting down...")
                break
        if data_received:
            # End time
            end_time = time.time()

            # Calculate elapsed time and throughput:
            elapsed_time = end_time - start_time
            total_file_size = sum(len(chunk) for chunk in file_chunks)  # calculate total file size
            file_size_bits = total_file_size * 8
            throughput = file_size_bits / elapsed_time
            throughput_mbps = throughput / 1000000
            print(f"The throughput is {throughput_mbps} Mbps")

            # Call the function to write chunks to file after the while loop
            write_chunks_to_file(file_chunks)

            data, addr = sock.recvfrom(4096)
            if data == b'FIN':
                print("FIN packet is received")
                sock.sendto(b'ACK', addr)
                print("ACK packet is sent")
                print("Connection terminated")
                sock.close()  # Close the socket
            
    except Exception as e:
        print(f"An error occurred: {e}")


else:
    print('Invalid option. Be cool and use a command bro')

