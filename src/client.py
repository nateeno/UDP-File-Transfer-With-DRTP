import socket
import struct
import time

from utils import *

# ---------------- CODE FOR CLIENT 

def read_file_data(file_path):
    """
    Reads and returns the data from a file.
    Args:
        file_path (str): The path to the file.
    Returns:
        bytes: The data read from the file.
    """
    try:
        with open(file_path, 'rb') as file:
            file_data = file.read()
        return file_data
    except FileNotFoundError:
        print(f"File {file_path} not found. Please check the file path and try again.")
        exit(1)
    except Exception as e:
        print(f"An error occurred while opening the file: {e}")
        exit(1)

SYN_ACK = b'SYN-ACK'
ACK = b'ACK'

def handle_connection(sock, buffer_size, server_ip, server_port):
    """
    Handles the connection setup with the server.
    Args:
        sock (socket): The socket to receive data from and send data to.
        buffer_size (int): The maximum amount of data to be received at once.
        server_ip (str): The IP address of the server.
        server_port (int): The port number of the server.
    Returns:
        bool: True if the connection is established, False otherwise.
    """
    global SYN_ACK, ACK
    try:
        data, addr = sock.recvfrom(buffer_size)
        if data == SYN_ACK:
            print("SYN-ACK packet is received")
            sock.sendto(ACK, (server_ip, server_port))
            print("ACK packet is sent")
            print("Connection established\n")
            return True
    except socket.timeout:
        print("Connection failed. The server is not responding.")
        sock.close()
        exit()
    return False

def client(args):
    """
    Starts a UDP client and handles file transfer to a server.
    Args:
        args (argparse.Namespace): The command line arguments.
    """
    UDP_IP = args.ip
    UDP_PORT = args.port
    WINDOW_SIZE = args.window

    try:
        print('Client started...')
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
        sock.settimeout(1.0)  # GBN timeout (1sec)

        file_data = read_file_data(args.file)

        # Define the size of the DRTP header
        header_size = struct.calcsize(header_format)

        # Calculate the size of the data chunk
        chunk_size = MAX_PACKET_SIZE - header_size

        # Split the file data into chunks 
        file_chunks = [file_data[i:i+chunk_size] for i in range(0, len(file_data), chunk_size)]

        print("Connection Establishment Phase:\n")

        sock.sendto(b'SYN', (UDP_IP, UDP_PORT))
        print("SYN packet is sent")

        connection_established = handle_connection(sock, BUFFER_SIZE, UDP_IP, UDP_PORT)
        if not connection_established:
            pass

        print("\nData Transfer:\n")

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

        print("\nDATA Finished")
        print("\nConnection Teardown Phase:")

        # After sending all packets
        sock.sendto(b'FIN', (UDP_IP, UDP_PORT))
        print(f"{time.strftime('%H:%M:%S')} -- FIN packet is sent")
        data, addr = sock.recvfrom(BUFFER_SIZE)
        if data == b'ACK':
            print("ACK packet is received")
            print("Connection terminated")
            sock.close()  # Close the socket
        
    except Exception as e:
        print(f"An error occurred: {e}")
    pass