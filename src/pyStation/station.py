import socket
import selectors
import types
import sys
import csv
import pathlib

# CONSTANTS
SERVER = "127.0.0.1"
FORMAT = "UTF-8"


class ServerConfig:
    def __init__(self, station, tcp_port, udp_port):
        self.STATION = station
        self.HEADER = 64
        self.TCP_PORT = tcp_port
        self.UDP_PORT = udp_port
        self.SERVER = SERVER
        self.TCP_ADDR = (self.SERVER, self.TCP_PORT)
        self.UDP_ADDR = (self.SERVER, self.UDP_PORT)
        self.FORMAT = FORMAT
        self.DISCONNECT_MESSAGE = "!DISCONNECT"

    def addCoordinates(self, x, y):
        self.x = x
        self.y = y


html_content = """
<form action="http://{host}:{port}" method="POST">
    <div>
        <h1>Welcome to {station}</h1><br>
        Hello {address} <br>
        <label for="station">What station would you like to go to?</label>
        <input name="Station" id="station">
    </div>
    <div>
        <label for="time">When do you want to leave?</label>
        <input name="time" id="time">
    </div>
    <div>
        <input type="submit" value="Get travel plan">
    </div>
</form>
"""


def accept_tcp_wrapper(sock, sel):
    conn, addr = sock.accept()  # Should be ready to read
    # print('accepted connection from', addr)
    conn.setblocking(False)
    # create a data object that holds addr, inb and outb
    data = types.SimpleNamespace(addr=addr, inb=b'', outb=b'')
    events = selectors.EVENT_READ | selectors.EVENT_WRITE
    # register the client socket
    sel.register(conn, events, data=data)


def getRequestBody(request_array):
    for index, item in enumerate(request_array):
        if item == "":
            return request_array[index + 1]


def service_tcp_connection(key, mask, sel, serverConfig):
    request = False
    method = "GET"
    sock = key.fileobj
    data = key.data
    # if the socket is ready for reading -- mask is True & selectors.EVENT_READ is True
    if mask & selectors.EVENT_READ:
        # receive the data
        recv_data = sock.recv(1024).decode(FORMAT)
        if recv_data:  # if recv_data is not None
            # data.outb += recv_data  # append received data to data.outb
            request = True
            method = recv_data.split()[0]
            print(f"Request method: {method}")
            requestBody = getRequestBody(recv_data.split("\r\n"))
            print(f"Request body: {requestBody}")
            # for index, item in enumerate(array):
            #     print(f"{index}: {item}")
            # print(f"Received data: {recv_data}\r\n\r\n")

        else:  # the client has closed their socket so the server should too.
            print('closing connection to', data.addr)
            sel.unregister(sock)
            sock.close()
    if mask & selectors.EVENT_WRITE:  # write the data back to the client
        # we have received, and now we can send
        if request:
            if method == "GET" or method == "POST":
                # print('echoing', repr(data.outb), 'to', data.addr)
                # sent = sock.send(data.outb)  # send data back to the client
                # data.outb = data.outb[sent:]  # remove sent data from data.outb
                sendData = "HTTP/1.1 200 OK\r\n"
                sendData += "Content-Type: text/html; charset=utf-8\r\n"
                sendData += "\r\n"
                sendData += html_content.format(station=serverConfig.STATION,
                                                address=data.addr,
                                                host=key.fileobj.getsockname()[
                                                    0],
                                                port=key.fileobj.getsockname()[1])
                sock.send(sendData.encode())
                request = False  # request fulfiled
                sel.unregister(sock)
                sock.close()


def startTcpPort(serverConfig, sel):
    # create TCP server socket
    tcpServerSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcpServerSocket.bind(serverConfig.TCP_ADDR)
    tcpServerSocket.listen()
    print(f"[LISTENING] TCP Server is listening on {serverConfig.TCP_ADDR}.")
    tcpServerSocket.setblocking(False)
    sel.register(tcpServerSocket, selectors.EVENT_READ, data=None)
    return tcpServerSocket


def startUdpPort(serverConfig, sel):
    # create UDP server socket
    udpServerSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udpServerSocket.bind(serverConfig.UDP_ADDR)
    print(f"[LISTENING] UDP Server is listening on {serverConfig.UDP_ADDR}.")
    sel.register(udpServerSocket, selectors.EVENT_READ, data=None)
    return udpServerSocket


def serveTcpUdpPort(serverConfig, sel, tcpServerSocket, udpServerSocket):
    # wait for connection
    try:
        while True:
            # wait unitl registered file objects become ready and set a selector with no timeout
            # the call will block until file object becomes ready -- either TCP or UDP has an EVENT_READ
            events = sel.select(timeout=None)

            for key, mask in events:
                # print(f"the key is: {key}.")
                # print(f"the sockname is: {key.fileobj.getsockname()}.")
                # print(f"the mask is: {mask}.")

                # a listening socket that hasn't been accepted yet i.e. no data
                if key.data is None:

                    # if the listening socket is TCP
                    if key.fileobj.getsockname() == serverConfig.TCP_ADDR:
                        # print("TCP accept wrapper!")
                        accept_tcp_wrapper(key.fileobj, sel)

                    # if the listening socket is UDP
                    if key.fileobj.getsockname() == serverConfig.UDP_ADDR:
                        # print("UDP received!")
                        bytesAddressPair = udpServerSocket.recvfrom(1024)
                        message = bytesAddressPair[0]
                        address = bytesAddressPair[1]
                        clientMsg = f"Message from Client:{message}"
                        clientIP = f"Client IP Address:{address}"
                        print(clientMsg)
                        print(clientIP)
                        udpServerSocket.sendto(
                            "Hello from server.".encode(), address)

                # a client socket that has been accepted and now we need to service it i.e. has data
                else:
                    if key.fileobj.getsockname() == serverConfig.TCP_ADDR:
                        # print("TCP service connection!")
                        service_tcp_connection(key, mask, sel, serverConfig)

            # conn, addr = tcpServerSocket.accept()  # accept new connection
            # handleTcpClient(serverConfig, conn, addr)
    except KeyboardInterrupt:
        print("Caught keyboard interrupt, exiting")
    finally:
        sel.close()


def acceptInputs(argv):
    if len(argv) == 0:
        print("Missing inputs.")
        sys.exit(2)

    stationName = argv[0]
    stationTcpPort = int(argv[1])  # tcp_port = 5050
    stationUdpPort = int(argv[2])  # udp_port = 6060

    serverConfig = ServerConfig(stationName, stationTcpPort, stationUdpPort)
    adjacentStation = argv[3:]

    return serverConfig, adjacentStation


def read_timetable(filepath):
    timetable = []
    rowCount = 0
    with open(filepath, 'r') as file:
        reader = csv.reader(file, delimiter=',')
        for row in reader:
            if rowCount == 0:
                stationCoordinates = row

            else:
                timetable.append(row)
            rowCount = rowCount+1

    return timetable, stationCoordinates


def main(argv):
    # store config and neighbours from inputs
    serverConfig, adjacentStation = acceptInputs(argv)
    print(f"Station Name: {serverConfig.STATION}")
    print(f"TCP_ADDR: {serverConfig.TCP_ADDR}")
    print(f"UDP_ADDR: {serverConfig.UDP_ADDR}")
    print(f"Adjacent station: {adjacentStation}")

    # Read CSV timetable file -- assume that all contents are correct
    path = str(pathlib.Path(__file__).parent.absolute()).replace(
        "\src\pyStation", f"\datafiles\\tt-{serverConfig.STATION}")
    print(path)
    timetable, stationCoordinates = read_timetable(path)
    serverConfig.addCoordinates(
        float(stationCoordinates[1]), float(stationCoordinates[2]))  # add coordinates
    print(f"X: {serverConfig.x} | Y : {serverConfig.y} ")
    print("timetable: ")
    for row in timetable:
        print(row)
    # Create selector
    sel = selectors.DefaultSelector()
    # Start TCP port
    tcpServerSocket = startTcpPort(serverConfig, sel)
    # Start UDP port
    udpServerSocket = startUdpPort(serverConfig, sel)
    # Serve TCP and UDP ports
    serveTcpUdpPort(serverConfig, sel, tcpServerSocket, udpServerSocket)

    return None


if __name__ == "__main__":
    main(sys.argv[1:])  #
