# UDP Client-Server Application

This is a simple UDP client-server application implemented in Python.

## Prerequisites

You need to have Python installed on your machine to run this application.

## Usage

### Server

To start the server, navigate to the `src` directory and run the following command:

```bash
python application.py --server --port 8080
```

The server will start and wait for incoming connections.

### Client

To start the client and send a file to the server, navigate to the `src` directory and run the following command:

```bash
python application.py --client --ip localhost --port 8080 --file img/test.jpg
```

The client will connect to the server and start sending the file.

### Optional arguments:

- Use `--window` to set the sliding window size
- Use `--discard` to set a sequence number to discard for retransmission test
