import argparse
import socket
import struct
import time

BUFFER_SIZE = 4096
MAX_PACKET_SIZE = 1000
header_format = '!HHH'  # sequence number, acknowledgment number, and flags are all 2 bytes

def get_args():
    # Initialize argument parser
    parser = argparse.ArgumentParser(description='UDP client and server')
    parser.add_argument('--client', '-c', action='store_true', help='Run as client')
    parser.add_argument('--server', '-s', action='store_true', help='Run as server')
    parser.add_argument('--ip', '-i', default='127.0.0.1', help='IP address of the server, default is 127.0.0.1')
    parser.add_argument('--port', '-p', type=int, default=8080, help='UDP port, default is 8080, should be in range 1024-65535')
    parser.add_argument('--file', '-f', type=str, help='File name')
    parser.add_argument('--window', '-w', type=int, default=3, help='Sliding window size')
    parser.add_argument('--discard', '-d', type=int, help='Seq number to discard for retransmission test')
    return parser.parse_args()


def validate_args(args):
    if args.server and args.client:
        print('Error: Cannot run the application in both server and client mode. Please choose one.')
        exit(1)

    if not 1024 <= args.port <= 65535:
        print("Error: Port number must be in the range 1024-65535")
        exit(1)