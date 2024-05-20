# ---------------- IMPORTS ---------------- 
# Import necessary utilities
from utils import *

# ---------------- UTILITY FUNCTIONS ---------------- 
# Functions for socket initiation, file handling, data receiving, and more.

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
    syn_ack_header = struct.pack(header_format, 0, 0, SYN_FLAG | ACK_FLAG)
    sock.sendto(syn_ack_header, addr)
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
    print(f"{datetime.now().strftime('%H:%M:%S.%f')} -- sending ack for the received {sequence_number}")


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
    _, _, flags = struct.unpack(header_format, data)
    if flags == FIN_FLAG:
        print("\nFIN packet is received")
        ack_header = struct.pack(header_format, 0, 0, ACK_FLAG)
        sock.sendto(ack_header, addr)
        print("FIN ACK packet is sent")
        print(f"\nThe throughput is {throughput_mbps} Mbps")
        print("Connection Closes")
        sock.close()

# ---------------- MAIN SERVER FUNCTION ---------------- 
# This function starts a UDP server and handles file transfer from a client.

def server(args):

    # Extract the IP, port, and sequence to discard from the argument parser
    UDP_IP = args.ip
    UDP_PORT = args.port
    DISCARD_SEQ = args.discard

    try:
        print(f'Server started on IP: {UDP_IP} and port: {UDP_PORT}')  

        # Create a UDP socket and bind it to the IP and port
        sock = init_socket(UDP_IP, UDP_PORT)

        # Initialize variables for the data transfer
        data_received = False
        ack_dict = {} 
        expected_sequence_number = 1
        buffer = {}  
        file_chunks = []  
        file_transfer_complete = False  
        header_size = struct.calcsize(header_format)

        while True: 
            try:
                # Receive data and check for flags
                data, addr = receive_data(sock, BUFFER_SIZE)
                _, _, flags = struct.unpack(header_format, data)

                # If the flag is SYN, handle connection establishment
                if flags == SYN_FLAG:
                    handle_syn(sock, addr)

                    # Wait for ACK from client to establish connection
                    data, addr = receive_data(sock, BUFFER_SIZE)
                    _, _, flags = struct.unpack(header_format, data)
                    if flags == ACK_FLAG:
                        print('ACK packet is received')
                        print('Connection Established\n')

                        # Start receiving data
                        start_time = time.time()
                        data_received = True

                        while True:
                            data, addr = receive_data(sock, BUFFER_SIZE)
                            sequence_number, _, flags, chunk = parse_data(data, header_size)

                            # Create an ACK for this sequence number if it doesn't already exist
                            if sequence_number not in ack_dict:
                                ack_dict[sequence_number] = struct.pack('!HHH', sequence_number, 0, 0)

                            # Handle the incoming data based on its sequence number
                            if sequence_number == DISCARD_SEQ:
                                print(f"{datetime.now().strftime('%H:%M:%S.%f')} -- Discarding packet with sequence number {DISCARD_SEQ}")
                                DISCARD_SEQ = float('inf')  
                            elif sequence_number == expected_sequence_number:
                                print(f"{datetime.now().strftime('%H:%M:%S.%f')} -- packet {sequence_number} is received")
                                file_chunks.append(chunk)  
                                send_acknowledgement(sock, addr, sequence_number, ack_dict)
                                expected_sequence_number += 1
                                
                                # If last packet, break the loop
                                if flags == FIN_FLAG:  
                                    file_transfer_complete = True  
                                    break

                                # Process any buffered packets with sequence numbers that match the expected one
                                while expected_sequence_number in buffer:
                                    data = buffer.pop(expected_sequence_number)
                                    sequence_number, _, flags, chunk = parse_data(data, header_size)
                                    file_chunks.append(chunk)  
                                    expected_sequence_number += 1
                            elif sequence_number < expected_sequence_number or sequence_number in buffer:
                                continue
                            else:
                                # If the packet is out of order, buffer it for later
                                buffer[sequence_number] = data
                                print(f"{datetime.now().strftime('%H:%M:%S.%f')} -- out-of-order packet {sequence_number} is received")
                        # If the file transfer is complete, break the loop
                        if file_transfer_complete:
                            break  

            except KeyboardInterrupt:
                print("\nServer interrupted by user. Shutting down...")
                break

        # If data was received, process it and calculate the throughput
        if data_received:
            end_time = time.time()
            elapsed_time = end_time - start_time
            total_file_size = sum(len(chunk) for chunk in file_chunks)  
            file_size_bits = total_file_size * 8
            throughput_mbps = calculate_throughput(elapsed_time, file_size_bits)
            write_chunks_to_file(file_chunks)
            handle_fin(sock, BUFFER_SIZE, throughput_mbps)  
            
    except Exception as e:
        print(f"An error occurred: {e}")
    pass
