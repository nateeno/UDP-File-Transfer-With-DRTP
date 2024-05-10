# UDP Client-Server Application

This is a simple UDP file transfer client-server application implemented in Python. It incorporates a sliding window protocol (DRTP) for reliable data transfer.
TEST 
## Usage

Here are some arguments: \
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

The server will start and wait for incoming connections.

### Client

To start the client and send a file to the server, navigate to the `src` directory and run the following command:

```bash
python application.py --client --file ./img/iceland_safiqul.jpg
```

The client will connect to the server and start sending the file.

### Optional arguments - window

```bash
python application.py --client --ip localhost --port 8080 --file ./img/iceland_safiqul.jpg --window
```

This command will start the client with a sliding window size of 5.

### Optional arguments - discard

```bash
python application.py --server --port 8080 --discard 8
```

This command starts the server and discards the packet with sequence number 8 for retransmission testing.

### Mininet

```bash
sudo mn --custom /home/nathaniel/DRTP/drtp-oppgave/simple-topo.py --topo NetworkTopo

```

```bash
mininet> xterm h1 h2
```

```bash
python3 application --server --ip 10.0.0.2 --port 8080
```

```bash
python3 application.py --client --ip 10.0.0.2 --port 8080 --file ./img/iceland_safiqul.jpg
```
