import socket
import selectors
import types
import sys
import csv
import pathlib
import json

# CONSTANTS
SERVER = "127.0.0.1"
FORMAT = "UTF-8"


class TimetableRecord:
    def __init__(self, departureTime, depatureLocation, arrivalTime, arrivalLocation):
        self.departureTime = departureTime
        self.depatureLocation = depatureLocation
        self.arrivalTime = arrivalTime
        self.arrivalLocation = arrivalLocation


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

    def addTimetable(self, timetable):
        self.timetable = timetable

    def addNeighbour(self, neighbours):
        self.neighbours = []
        for neighbour in neighbours:
            self.neighbours.append((self.SERVER, int(neighbour)))


class StationMessage:
    def __init__(self, sourceName, destinationName, sourceAddress, destinationAddress):
        self.sourceName = sourceName
        self.destinationName = destinationName
        self.sourceAddress = sourceAddress
        self.destinationAddress = destinationAddress


html_content = """
<!DOCTYPE html>
<html>
    <head>
        <title>Transperth Journey Planner</title>
        <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.5.1/jquery.min.js"></script>
        <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.4.1/css/bootstrap.min.css" integrity="sha384-Vkoo8x4CGsO3+Hhxv8T/Q5PaXtkKtu6ug5TOeNV6gBiFeWPGFN9MuhOf23Q9Ifjh" crossorigin="anonymous">
    </head>
    <body>
        <div class="container">
            <h1>Welcome to {station}</h1><br>
            Hello {address} <br>
            <form action="http://{host}:{port}" method="POST">
                <div>
                    <label for="station">What station would you like to go to?</label>
                    <input name="station" id="station" class="form-control">
                </div>
                <div>
                    <label for="time">When do you want to leave?</label>
                    <select name="time" id="timetable" class="form-control"></select>
                </div>
                <div>
                    <input type="submit" value="Get travel plan" class="btn btn-primary">
                </div>
            </form>
        </div>
    </body>
</html>

<script type="text/javascript">

    const timetable = {timetable};

    const updateTimetable = ($timetable) => {{
        timetable.map(record => $('<option>')
            .attr({{ value : record[0] }})
            .text(record[0])
        ).forEach($option => $timetable.append($option));
    }}

    $(() => {{
        const $timetable = $("#timetable");
        console.log($timetable);
        updateTimetable($timetable);
    }});
</script>
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


def getRequestObject(request_body):
    request_body_objects = []
    request_body = request_body.split("&")
    for item in request_body:
        pair = item.split("=")
        request_body_objects.append({pair[0]: pair[1]})
    return request_body_objects


def send_udp(key, mask, sel, serverConfig, msg, udpServerSocket):
    neighbours = serverConfig.neighbours
    msg = json.dumps(msg)
    message = msg.encode(FORMAT)
    msg_length = len(message)
    send_length = str(msg_length).encode(FORMAT)
    send_length += b" " * (serverConfig.HEADER - len(send_length))

    # send to each neighbour
    for neighbour in neighbours:
        print(f"neighbour: {neighbour}")
        udpServerSocket.sendto(send_length, neighbour)
        udpServerSocket.sendto(message, neighbour)


def service_tcp_connection(key, mask, sel, serverConfig, udpServerSocket):
    request = False
    method = "GET"
    sock = key.fileobj
    data = key.data
    # if the socket is ready for reading -- mask is True & selectors.EVENT_READ is True
    if mask & selectors.EVENT_READ:
        # receive the data
        recv_data = sock.recv(1024).decode(FORMAT)
        if recv_data:  # if recv_data is not None
            request = True
            method = recv_data.split()[0]
            print(f"Request method: {method}")
            requestBody = getRequestBody(recv_data.split("\r\n"))
            print(f"Request body: {requestBody}")
            if method == "POST":
                requestObject = getRequestObject(requestBody)
                print(f"Request objects: {requestObject}")
                send_udp(key, mask, sel, serverConfig,
                         requestObject, udpServerSocket)

        else:  # the client has closed their socket so the server should too.
            print('closing connection to', data.addr)
            sel.unregister(sock)
            sock.close()
    if mask & selectors.EVENT_WRITE:  # write the data back to the client
        # we have received, and now we can send
        if request:
            if method == "GET" or method == "POST":
                sendData = "HTTP/1.1 200 OK\r\n"
                sendData += "Content-Type: text/html; charset=utf-8\r\n"
                sendData += "\r\n"
                sendData += html_content.format(station=serverConfig.STATION,
                                                timetable=serverConfig.timetable,
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
                        bytesAddressPair = udpServerSocket.recvfrom(
                            serverConfig.HEADER)
                        message_length = bytesAddressPair[0].decode()
                        bytesAddressPair = udpServerSocket.recvfrom(
                            serverConfig.HEADER)
                        print(f"Message length: {message_length}")
                        message = bytesAddressPair[0].decode()
                        address = bytesAddressPair[1]

                        clientMsg = f"Message from Client:{message}"
                        clientIP = f"Client IP Address:{address}"
                        print(clientMsg)
                        print(clientIP)
                        # udpServerSocket.sendto(
                        #     "Hello from server.".encode(), address)

                # a client socket that has been accepted and now we need to service it i.e. has data
                else:
                    if key.fileobj.getsockname() == serverConfig.TCP_ADDR:
                        # print("TCP service connection!")
                        service_tcp_connection(
                            key, mask, sel, serverConfig, udpServerSocket)

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
    stationTcpPort = int(argv[1])  # e.g. tcp_port = 5050
    stationUdpPort = int(argv[2])  # e.g. udp_port = 6060

    serverConfig = ServerConfig(stationName, stationTcpPort, stationUdpPort)
    neighbourStation = argv[3:]
    serverConfig.addNeighbour(neighbourStation)

    return serverConfig


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
    serverConfig = acceptInputs(argv)
    print(f"Station Name: {serverConfig.STATION}")
    print(f"TCP_ADDR: {serverConfig.TCP_ADDR}")
    print(f"UDP_ADDR: {serverConfig.UDP_ADDR}")
    print(f"Neighbour station: {serverConfig.neighbours}")

    # TODO: ability to detect that a timetable file has changed, to delete/dispose of the previous information, and move to using the new information
    # Read CSV timetable file -- assume that all contents are correct
    path = str(pathlib.Path(__file__).parent.absolute()).replace(
        "\src\pyStation", f"\datafiles\\tt-{serverConfig.STATION}")
    print(path)
    timetable, stationCoordinates = read_timetable(path)
    serverConfig.addCoordinates(
        float(stationCoordinates[1]), float(stationCoordinates[2]))  # add coordinates
    print(f"X: {serverConfig.x} | Y : {serverConfig.y} ")
    serverConfig.addTimetable(timetable)
    print("timetable: ")
    svrTimetable = serverConfig.timetable
    for row in svrTimetable:
        print(row)
    # Create selector
    sel = selectors.DefaultSelector()
    # Start TCP port
    tcpServerSocket = startTcpPort(serverConfig, sel)
    # Start UDP port
    udpServerSocket = startUdpPort(serverConfig, sel)
    # Serve TCP and UDP ports
    serveTcpUdpPort(serverConfig, sel, tcpServerSocket, udpServerSocket)
    # TODO: Design and implementation of a simple programming language independent protocol to exchange queries,
    # responses, and (possibly) control information between stations.
    # TODO: Ability to find a valid (but not necessarily optimal) route between origin and destination stations,
    # for varying sized transport-networks of 2, 3, 5, 10, and 20 stations (including transport-networks involving cycles),
    # with no station attempting to collate information about the whole transport-network; ability to support multiple, concurrent queries from different clients.
    # TODO: Ability to detect and report when a valid route does not exist (on the current day).
    return None


if __name__ == "__main__":
    main(sys.argv[1:])
