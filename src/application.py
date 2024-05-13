from client import client
from server import server
from utils import get_args, validate_args

def main():
    """
    Entry point of the script. 
    Parses and validates the command-line arguments, then starts the client or server as specified.
    """
    args = get_args()
    validate_args(args)

    if args.client:
        client(args)
    elif args.server:
        server(args)
    else:
        print('Invalid option. Be cool and use a command bro')

if __name__ == "__main__":
    """
    Checks if the script is being run directly (instead of being imported), 
    and if so, calls the main function.
    """
    main()