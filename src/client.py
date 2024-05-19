# ---------------- IMPORTS ---------------- 
# Import necessary utilities
from utils import *

# ---------------- UTILITY FUNCTIONS FOR CLIENT ---------------- 
# Functions for file reading, server connection, and client operations.

def read_file_data(file_path):
    """
    Reads and returns the data from a file.
    Args:
        file_path (str): The path to the file.
    Returns:
        bytes: The data read from the file.
    """
    if not os.path.isfile(file_path):
        print(f"Error: File {file_path} does not exist.")
        exit(1)
    try:
        with open(file_path, 'rb') as file:
            file_data = file.read()
        return file_data
    except Exception as e:
        print(f"An error occurred while opening the file: {e}")
        exit(1)


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
    try:
        data, _ = sock.recvfrom(buffer_size)
        _, _, flags = struct.unpack('!HHH', data)  # Unpack the flags
        if flags == (SYN_FLAG | ACK_FLAG):  # Check for SYN-ACK flag
            print("SYN-ACK packet is received")
            ack_header = struct.pack(header_format, 0, 0, ACK_FLAG)
            sock.sendto(ack_header, (server_ip, server_port))
            print("ACK packet is sent")
            print("Connection established\n")
            return True
    except socket.timeout:
        print("Connection failed. The server is not responding.")
        sock.close()
        exit()
    return False


# ---------------- MAIN CLIENT FUNCTION ---------------- 
# This function starts a UDP client and handles file transfer to a server.

def client(args):
    """
    Starts a UDP client and handles file transfer to a server.
    Args:
        args (argparse.Namespace): The command line arguments.
    """
    
    # Extract the IP, port, and window size from the argument parser
    UDP_IP = args.ip
    UDP_PORT = args.port
    WINDOW_SIZE = args.window

    try:
        print('Client started...')
        
        # Create a UDP socket and set a timeout
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
        sock.settimeout(1.0)  # GBN timeout (1sec)

        # Read the file data and create chunks to send  
        file_data = read_file_data(args.file)
        header_size = struct.calcsize(header_format)
        chunk_size = MAX_PACKET_SIZE - header_size
        file_chunks = [file_data[i:i+chunk_size] for i in range(0, len(file_data), chunk_size)]

        # Begin the connection establishment phase
        print("Connection Establishment Phase:\n")
        syn_header = struct.pack(header_format, 0, 0, SYN_FLAG)
        sock.sendto(syn_header, (UDP_IP, UDP_PORT))
        print("SYN packet is sent")

        # Handle the connection with the server
        connection_established = handle_connection(sock, BUFFER_SIZE, UDP_IP, UDP_PORT)
        if not connection_established:
            print("Error: Failed to establish connection.")
            exit(1)

        print("\nData Transfer:\n")

        # Begin the data transfer phase
        base = 1
        nextseqnum = 1
        frame_buffer = [None] * WINDOW_SIZE
        window_packets = []

        # While there are chunks left to send
        while base <= len(file_chunks):
            # Send all the chunks within the window
            while nextseqnum < base + WINDOW_SIZE and nextseqnum <= len(file_chunks):
                # Create packet and send it
                flags = FIN_FLAG if nextseqnum == len(file_chunks) else ACK_FLAG 
                header = struct.pack(header_format, nextseqnum, 0, flags)
                packet = header + file_chunks[nextseqnum - 1]
                frame_buffer[(nextseqnum - 1) % WINDOW_SIZE] = packet
                window_packets.append(nextseqnum)
                sock.sendto(packet, (UDP_IP, UDP_PORT))
                print(f"{datetime.now().strftime('%H:%M:%S.%f')} -- packet with seq = {nextseqnum} is sent, sliding window = {window_packets}")
                nextseqnum += 1

            # Wait for acknowledgements
            try:
                data, _ = sock.recvfrom(BUFFER_SIZE)
                ack, _, _ = struct.unpack('!HHH', data)  
                print(f"{datetime.now().strftime('%H:%M:%S.%f')} -- ACK for packet {ack} received")

                # If the ack is within the window, move the base of the window
                if ack >= base and ack < nextseqnum:
                    window_packets = [seq for seq in window_packets if seq > ack]
                    base = ack + 1
            except socket.timeout:
                # If a timeout occurs, retransmit all unacknowledged frames
                print(f"{datetime.now().strftime('%H:%M:%S.%f')} -- RTO occurred")
                for i in range(base, nextseqnum):
                    sock.sendto(frame_buffer[(i - 1) % WINDOW_SIZE], (UDP_IP, UDP_PORT))
                    print(f"{datetime.now().strftime('%H:%M:%S.%f')} -- retransmitting packet with seq = {i}")

        print("\nDATA Finished")
        print("\nConnection Teardown Phase:")

        # After all packets are sent, begin the connection teardown phase
        fin_header = struct.pack(header_format, 0, 0, FIN_FLAG)
        sock.sendto(fin_header, (UDP_IP, UDP_PORT))
        print(f"{datetime.now().strftime('%H:%M:%S.%f')} -- FIN packet is sent")

        # Wait for the final acknowledgement, then close the connection
        data, _ = sock.recvfrom(BUFFER_SIZE)
        if data == b'ACK':
            print("ACK packet is received")
            print("Connection terminated")
            sock.close()
        
    except Exception as e:
        print(f"An error occurred: {e}")
    pass