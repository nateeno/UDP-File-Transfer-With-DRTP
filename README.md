# UDP Client-Server Application

This Python application allows a file transfer between a client and a server using User Datagram
Protocol (UDP). Users can specify the operation mode, server's IP and port, filename, window size,
and a sequence number for discard testing through command-line inputs. The file set for transfer is
segmented into chunks at the client end. Each chunk is then encapsulated within a Data Reliable
Transfer Protocol (DRTP) header before being dispatched to the server.

To guarantee data reliability, the application uses a sliding window protocol. This allows for the
retransmission of any unacknowledged packets. Additionally, an out-of-order packet buffer is
implemented on the server side to ensure proper data sequencing.

The application calculates and displays the file transfer's throughput to provide a measure of data
transmission speed.

## Arguments

The following arguments can be used: \
`--client` to run the application as a client \
`--server` to run the application as a server \
`--ip` to specify the IP address of the server \
`--port` to specify the UDP port \
`--file` to spescify the file name to be transferred _(client mode only)_\
`--window` to set the sliding window size _(client mode)_ \
`--discard` to set a sequence number to discard for retransmission test _(server mode)_

### Server

To start the server, navigate to the `src` directory and run the following command:

```bash
python application.py -s
```

The server will now start with IP set to 10.0.1.2 and on port 8080, and wait for incoming connections. \
Use `python application.py -s -i 127.0.0.1` to start the server on localhost.

### Client

To start the client and send a file to the server, navigate to the `src` directory and run the following command:

```bash
python application.py -c -f ./img/file.jpg
```

The client will connect to the server with the IP set to 10.0.1.2 and port 8080 and start sending the file with windowside 3.\
Use `python application.py -c -i 127.0.0.1 -f ./img/iceland_safiqul.jpg` to start the client on localhost.

### Optional arguments - window

```bash
python application.py -c -f ./img/iceland_safiqul.jpg --window 5
```

This command will start the client with a sliding window size of the given number.

### Optional arguments - discard

```bash
python application.py --server -d 8
```

This command starts the server and discards the packet with sequence number of the given number for retransmission testing.

### Mininet

Mininet is a network emulator used to test the UDP client-server application.\
It creates a network of virtual hosts and links. The `topologies/simple-topo.py` script is used to define the network topology.

```bash
python3 topologies/simple-topo.py
```

```bash
mininet> xterm h1 h2

# start the server and client
Node:h2> python3 application -s
Node:h1> python3 application.py -c-f ./img/iceland_safiqul.jpg
```

The server and client will with this start on the default ip: 10.0.1.2 and port:8080
