# UDP Client-Server Applicationadd .

This is a simple UDP file transfer client-server application implemented in Python. It incorporates a sliding window protocol (DRTP) for reliable data transfer.

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
python application.py --server
```

The server will now start with IP set to 127.0.0.1 and on port 8080, and wait for incoming connections.

### Client

To start the client and send a file to the server, navigate to the `src` directory and run the following command:

```bash
python application.py --client --file ./img/iceland_safiqul.jpg
```

The client will connect to the server with the IP set to 127.0.0.1 and port 8080 and start sending the file with windowside 4.

### Optional arguments - window

```bash
python application.py --client --ip localhost --port 8080 --file ./img/iceland_safiqul.jpg --window 'x'
```

This command will start the client with a sliding window size of 'x'.

### Optional arguments - discard

```bash
python application.py --server --port 8080 --discard 8
```

This command starts the server and discards the packet with sequence number 8 for retransmission testing.

### Mininet

```bash
cd src/topologies
sudo mn python3 simple-topo.py
```

```bash
mininet> xterm h1 h2
```

```bash
Node:h1> python3 application --server --ip 10.0.0.1 --port 8080
```

```bash
Node:h2> python3 application.py --client --ip 10.0.0.1 --port 8080 --file ./img/iceland_safiqul.jpg
```
