# ---------------- IMPORTS ---------------- 
# Import necessary modules for command line input, network communication, 
# handling binary data, operating system tasks, and time functions
import argparse
import socket
import struct
import os
import time
from datetime import datetime

# ---------------- CONSTANTS ---------------- 
# BUFFER_SIZE and MAX_PACKET_SIZE define the size limits for network data transfer
BUFFER_SIZE = 4096
MAX_PACKET_SIZE = 1000

# ---------------- HEADER FORMATTING ---------------- 
# Defines the format for data packet headers and flags for ACK, SYN, and FIN signals
header_format = '!HHH'  # sequence number, acknowledgment number, and flags (all 2 bytes)
ACK_FLAG = 1 << 2   # Flag for ACK signal
SYN_FLAG = 1 << 3   # Flag for SYN signal
FIN_FLAG = 1 << 1   # Flag for FIN signal

# ---------------- MAIN CODE ---------------- 
# This section will contain primary functionality of the program

def get_args():
    """
    Initializes the argument parser and parses the command line arguments.
    
    The function supports the following arguments: client, server, ip, file, window, discard
    
    Returns:
        argparse.Namespace: The command line arguments.
    """
    parser = argparse.ArgumentParser(description='UDP client and server')
    parser.add_argument('--client', '-c', action='store_true', help='Run as client')
    parser.add_argument('--server', '-s', action='store_true', help='Run as server')
    parser.add_argument('--ip', '-i', default='10.0.1.2', help='IP address of the server, default is 10.0.1.2')
    parser.add_argument('--port', '-p', type=int, default=8080, help='UDP port, default is 8080, should be in range 1024-65535')
    parser.add_argument('--file', '-f', type=str, help='File name')
    parser.add_argument('--window', '-w', type=int, default=3, help='Sliding window size')
    parser.add_argument('--discard', '-d', type=int, help='Seq number to discard for retransmission test')
    return parser.parse_args()

def validate_args(args):
    """
    Validates the command line arguments for the application.
    Args:
        args (argparse.Namespace): The command line arguments parsed by argparse.
    Returns:
        None. If any of the arguments are invalid, the function will print an error message and terminate the program.
    """

    # The application cannot run in both server and client mode at the same time
    if args.server and args.client:
        print('Error: Cannot run the application in both server and client mode. Please choose one.')
        exit(1)

    # The port number must be in the range 1024-65535
    if not 1024 <= args.port <= 65535:
        print("Error: Port number must be in the range 1024-65535")
        exit(1)
    
    # The window size must be in the range 1-100
    if not 1 <= args.window <= 100:
        print("Error: Window size must be in the range 1-100")
        exit(1)

    # If the application is running in client mode, a file must be specified
    if args.client and not args.file:
        print("Error: A file must be specified with the --file option in client mode.")
        exit(1)
    
    # If the application is running in server mode, a file should not be specified
    if args.server and args.file:
        print("Error: Cannot specify a file with the --file option in server mode.")
        exit(1)

    # The client mode should not receive a discard sequence number argument
    if args.client and args.discard:
        print("Error: Client mode should not receive a --discard argument.")
        exit(1)