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
python application.py --client --ip localhost --port 8080 --file ./img/iceland_safiqul.jpg
```

The client will connect to the server and start sending the file.

### Optional arguments:

- Use `--window` to set the sliding window size
- Use `--discard` to set a sequence number to discard for retransmission test

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
