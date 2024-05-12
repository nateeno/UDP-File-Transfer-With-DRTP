import argparse
import socket
import struct
import time

# Define constants
BUFFER_SIZE = 4096
MAX_PACKET_SIZE = 1000

# Initialize argument parser
parser = argparse.ArgumentParser(description='UDP client and server')
parser.add_argument('--client', '-c', action='store_true', help='Run as client')
parser.add_argument('--server', '-s', action='store_true', help='Run as server')
parser.add_argument('--ip', '-i', help='IP address of the server, default is 127.0.0.1')
parser.add_argument('--port', '-p', type=int, help='UDP port, default is 8080, should be in range 1024-65535')
parser.add_argument('--file', '-f', type=str, help='File name')
parser.add_argument('--window', '-w', type=int, default=3, help='Sliding window size')
parser.add_argument('--discard', '-d', type=int, help='Seq number to discard for retransmission test')
args = parser.parse_args()

# Define header fields
header_format = '!HHH'  # sequence number, acknowledgment number, and flags are all 2 bytes
sequence_number = 2
acknowledgment_number = 2
flags = 2
file_size = 0

# Construct DRTP header
header = struct.pack(header_format, sequence_number, acknowledgment_number, flags)

# Parse command-line arguments and validate
UDP_IP = args.ip or "127.0.0.1"
UDP_PORT = args.port or 8080
WINDOW_SIZE = args.window
DISCARD_SEQ = args.discard

"""
Validation of command-line arguments
"""

if args.server and args.client:
    print('Error: Cannot run the application in both server and client mode. Please choose one.')
    exit(1)

if not 1024 <= UDP_PORT <= 65535:
    print("Error: Port number must be in the range 1024-65535")
    exit(1)

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
Code for the client
"""

if args.client:
    try:
        print('Client started...')
        print("UDP target IP: %s" % UDP_IP)
        print("UDP target port: %s\n\n" % UDP_PORT)
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

        print(f'Number of packets: {len(file_chunks)}')
        print("Connection Establishment Phase:")

        # Three-way handshake
        sock.sendto(b'SYN', (UDP_IP, UDP_PORT))
        print("SYN packet is sent\n")
        try:
            data, addr = sock.recvfrom(BUFFER_SIZE)
            if data == b'SYN-ACK':
                print("SYN-ACK packet is received")
                sock.sendto(b'ACK', (UDP_IP, UDP_PORT))
                print("ACK packet is sent")
                print("Connection established")
        except socket.timeout:
            print("Connection failed. The server is not responding.")
            sock.close()
            exit()

        # Start GBN, after connection 
        sequence_number = 1

        # Sliding window implementation
        base = 1
        nextseqnum = 1
        #window_size = WINDOW_SIZE
        frame_buffer = [None] * WINDOW_SIZE

        window_packets = []
        while base <= len(file_chunks):
            while nextseqnum < base + WINDOW_SIZE and nextseqnum <= len(file_chunks):
                # Create DRTP header and packet
                flags = 1 if nextseqnum == len(file_chunks) else 0  # set flag to 1 if this is the last chunk
                header = struct.pack(header_format, nextseqnum, 0, flags)
                packet = header + file_chunks[nextseqnum - 1]
                
                # Store the packet in the frame buffer
                frame_buffer[(nextseqnum - 1) % WINDOW_SIZE] = packet

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
                print(f"ACK for packet {ack} received")

                if ack >= base and ack < nextseqnum:
                    window_packets = [seq for seq in window_packets if seq > ack]

                    base = ack + 1
            except socket.timeout:
                # If timeout, retransmit all unacknowledged frames
                print(f"{time.strftime('%H:%M:%S')} -- RTO occurred")
                for i in range(base, nextseqnum):
                    sock.sendto(frame_buffer[(i - 1) % WINDOW_SIZE], (UDP_IP, UDP_PORT))
                    print(f"{time.strftime('%H:%M:%S')} -- retransmitting packet with seq = {i}")

        # After sending all packets
        sock.sendto(b'FIN', (UDP_IP, UDP_PORT))
        print(f"{time.strftime('%H:%M:%S')} -- FIN packet is sent")
        data, addr = sock.recvfrom(4096)
        if data == b'ACK':
            print("ACK packet is received")
            print("Connection terminated")
            sock.close()  # Close the socket
        
    except Exception as e:
        print(f"An error occurred: {e}")


    """
    Code for the server!
    """

elif args.server:
    try:
        print(f'Server started on IP: {UDP_IP} and port: {UDP_PORT}')  

        data_received = False

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP 
            sock.bind((UDP_IP, UDP_PORT))
        except socket.error as e:
            print(f"Error creating/binding socket: {e}")
            exit(1)

        expected_sequence_number = 1

        buffer = {}  
        file_chunks = []  

        file_transfer_complete = False  

        # Define the size of the DRTP header
        header_size = struct.calcsize(header_format)

        while True: 
            try:
                data, addr = sock.recvfrom(BUFFER_SIZE) 
                if data == b'SYN':
                    print("SYN packet is received")
                    sock.sendto(b'SYN-ACK', addr)
                    print("SYN-ACK packet is sent")

                    data, addr = sock.recvfrom(BUFFER_SIZE)
                    if data == b'ACK':
                        print('Connection Established (yey)')

                        # START TIME: 
                        start_time = time.time()
                        data_received = True

                        # Start receiving file chunks
                        while True:
                            data, addr = sock.recvfrom(BUFFER_SIZE)
                            header = data[:header_size]
                            sequence_number, acknowledgment_number, flags = struct.unpack(header_format, header)
                            chunk = data[header_size:]

                            # If sequence_number is what we expected, send an ACK back
                            # If sequence_number is what we expected, send an ACK back
                            if sequence_number == expected_sequence_number:
                                if sequence_number == DISCARD_SEQ:
                                    print(f"Discarding packet with sequence number {DISCARD_SEQ}")
                                    time.sleep(1.5)  # artificial delay
                                else:
                                    print(f"{time.strftime('%H:%M:%S')} -- packet {sequence_number} is received")

                                    file_chunks.append(chunk)  # Add the chunk to the list
                                    ack = struct.pack('!H', sequence_number)  # pack sequence number into binary
                                    sock.sendto(ack, addr)  # send acknowledgment
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
                                print(f"{time.strftime('%H:%M:%S')} -- out-of-order packet {sequence_number} is received")

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
            throughput_mbps = round(throughput / 1000000, 2)  # round to 2 decimal places
            print(f"The throughput is {throughput_mbps} Mbps")

            # Call the function to write chunks to file after the while loop
            write_chunks_to_file(file_chunks)

            data, addr = sock.recvfrom(4096)
            if data == b'FIN':
                print("FIN packet is received")
                sock.sendto(b'ACK', addr)
                print("ACK packet is sent")
                print("Connection terminated")
                sock.close()
            
    except Exception as e:
        print(f"An error occurred: {e}")

else:
    print('Invalid option. Be cool and use a command bro')