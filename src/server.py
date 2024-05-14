import socket
import struct
import time

from utils import *

# ---------------- CODE FOR SERVER 

def init_socket(ip, port):
    """
    Creates and binds a UDP socket to the given IP and port.
    Args:
        ip (str): The IP address for the socket to bind to.
        port (int): The port for the socket to bind to.
    Returns:
        socket: The created and bound socket.
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # UDP
        sock.bind((ip, port))
        return sock
    except socket.error as e:
        print(f"Error creating/binding socket: {e}")
        exit(1)


def write_chunks_to_file(file_chunks):
    """
    Writes chunks of data to a file.
    Args:
        file_chunks (list): The chunks of data to write to the file.
    """
    try:
        with open('img/received_file.jpg', 'wb') as file:
            for chunk in file_chunks:
                file.write(chunk)
    except Exception as e:
        print(f"Error writing to file: {e}")
        exit(1)

def receive_data(sock, buffer_size):
    """
    Receives data from a socket.
    Args:
        sock (socket): The socket to receive data from.
        buffer_size (int): The maximum amount of data to be received at once.

    Returns:
        tuple: The received data and the sender's address.
    """
    data, addr = sock.recvfrom(buffer_size)
    return data, addr


def handle_syn(sock, addr):
    """
    Handles a SYN packet.
    Args:
        sock (socket): The socket to send data to.
        addr (tuple): The address of the recipient.
    """
    print("SYN packet is received")
    sock.sendto(b'SYN-ACK', addr)
    print("SYN-ACK packet is sent\n")


def parse_data(data, header_size):
    """
    Parses data into a header and body.
    Args:
        data (bytes): The data to parse.
        header_size (int): The size of the header.
    Returns:
        tuple: The sequence number, acknowledgment number, flags, and body.
    """
    header = data[:header_size]
    sequence_number, acknowledgment_number, flags = struct.unpack(header_format, header)
    chunk = data[header_size:]
    return sequence_number, acknowledgment_number, flags, chunk


def send_acknowledgement(sock, addr, sequence_number, acknowledgement_dictionary):
    """
    Sends an acknowledgement packet.
    Args:
        sock (socket): The socket to send data to.
        addr (tuple): The address of the recipient.
        sequence_number (int): The sequence number to acknowledge.
        acknowledgement_dictionary (dict): A dictionary that maps sequence numbers to acknowledgements.
    """
    sock.sendto(acknowledgement_dictionary[sequence_number], addr)
    print(f"sending ack for the received {sequence_number}")


def calculate_throughput(elapsed_time, file_size_bits):
    """
    Calculates the throughput of the transfer.
    Args:
        elapsed_time (float): The time it took to transfer the file.
        file_size_bits (int): The size of the file in bits.
    Returns:
        float: The throughput of the transfer in Mbps.
    """
    throughput = file_size_bits / elapsed_time
    throughput_mbps = round(throughput / 1000000, 2)  # round to 2 decimal places
    return throughput_mbps


def handle_fin(sock, buffer_size, throughput_mbps):
    """
    Handles a FIN packet.
    Args:
        sock (socket): The socket to receive data from and send data to.
        buffer_size (int): The maximum amount of data to be received at once.
        throughput_mbps (float): The throughput of the transfer.
    """
    data, addr = sock.recvfrom(buffer_size)
    if data == b'FIN':
        print("\nFIN packet is received")
        sock.sendto(b'ACK', addr)
        print("ACK packet is sent")
        print(f"\nThe throughput is {throughput_mbps} Mbps")
        print("Connection Closes")
        sock.close()

# ---------------- SERVER 

def server(args):
    """
    Starts a UDP server and handles file transfer from a client.
    Args:
        args (argparse.Namespace): The command line arguments.
    """
    UDP_IP = args.ip
    UDP_PORT = args.port
    DISCARD_SEQ = args.discard

    try:
        print(f'Server started on IP: {UDP_IP} and port: {UDP_PORT}')  

        data_received = False
        ack_dict = {}  # Dictionary to store the sequence numbers and their ACKs

        sock = init_socket(UDP_IP, UDP_PORT)

        expected_sequence_number = 1

        buffer = {}  
        file_chunks = []  

        file_transfer_complete = False  

        # Define the size of the DRTP header
        header_size = struct.calcsize(header_format)

        while True: 
            try:
                data, addr = receive_data(sock, BUFFER_SIZE)
                if data == b'SYN':
                    handle_syn(sock, addr)

                    data, addr = receive_data(sock, BUFFER_SIZE)
                    if data == b'ACK':
                        print('ACK packet is received')
                        print('Connection Established\n')

                        # START TIME: 
                        start_time = time.time()
                        data_received = True

                        # Start receiving file chunks

                        while True:
                            data, addr = receive_data(sock, BUFFER_SIZE)
                            sequence_number, acknowledgment_number, flags, chunk = parse_data(data, header_size)

                            if sequence_number not in ack_dict:
                                ack_dict[sequence_number] = struct.pack('!H', sequence_number)

                            # If sequence_number is what we expected, send an ACK back
                            if sequence_number == DISCARD_SEQ:
                                print(f"Discarding packet with sequence number {DISCARD_SEQ}")
                                DISCARD_SEQ = float('inf')  # Set the discard sequence to an infinitely large number
                            elif sequence_number == expected_sequence_number:
                                print(f"{time.strftime('%H:%M:%S')} -- packet {sequence_number} is received")
                                file_chunks.append(chunk)  # Add the chunk to the list

                                send_acknowledgement(sock, addr, sequence_number, ack_dict)

                                expected_sequence_number += 1

                                # If this was the last packet, break the loop
                                if flags == 1:
                                    file_transfer_complete = True  
                                    break

                                # Check if the next packet is in the buffer
                                while expected_sequence_number in buffer:
                                    data = buffer.pop(expected_sequence_number)
                                    sequence_number, acknowledgment_number, flags, chunk = parse_data(data, header_size)
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
            throughput_mbps = calculate_throughput(elapsed_time, file_size_bits)

            # Call the function to write chunks to file after the while loop
            write_chunks_to_file(file_chunks)

            handle_fin(sock, BUFFER_SIZE, throughput_mbps)
            
    except Exception as e:
        print(f"An error occurred: {e}")
    pass
