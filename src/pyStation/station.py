import socket
import selectors
import types
import sys
import csv
import pathlib
import json
import time as ts
import urllib
from datetime import datetime

# CONSTANTS
SERVER = "127.0.0.1"
FORMAT = "UTF-8"
TRIP_TYPE = ["FastestTrip", "LeastTransfers"]
HEADER_SIZE = 64


class Station:
    def __init__(self, station, tcp_port, udp_port):
        self.stationName = station
        self.HeaderSize = HEADER_SIZE
        if tcp_port == None:
            self.tcp_port = 0
        else:
            self.tcp_port = int(tcp_port)
        if udp_port == None:
            self.udp_port = 0
        else:
            self.udp_port = int(udp_port)
        self.server = SERVER
        self.tcp_address = (self.server, self.tcp_port)
        self.udp_address = (self.server, self.udp_port)
        self.format = FORMAT
        self.neighbours = []

    def addCoordinates(self, x, y):
        self.x = x
        self.y = y

    def addTimetable(self, timetable):
        self.timetable = timetable

    def addNeighbour(self, neighbour):
        self.neighbours.append(neighbour)

    def convertTimetableToString(self):
        string = "["
        for item in self.timetable:
            string += str(item) + ", "
        string = string + "]"
        return string

    def getStationUDPAddress(self):
        return f"http://{self.server}:{self.udp_port}"

    def getStationTCPAddress(self):
        return f"http://{self.server}:{self.tcp_port}"

    def getEarliestTrip(self, time):
        for timetableRecord in self.timetable:
            timeValue = datetime.strptime(time, "%H:%M")
            timetableRecordValue = datetime.strptime(
                timetableRecord[0], "%H:%M")
            if timetableRecordValue >= timeValue:
                return timetableRecord[0]

    def getStationString(self, timestamp, time):
        return f'{{ "stationName" : "{self.stationName}", \
                    "timestamp" : "{timestamp}" , \
                    "stationUDPAddress": "{self.getStationUDPAddress()}", \
                    "earliestTrip": "{self.getEarliestTrip(time)}" \
            }}'


class MessageSentLog:
    def __init__(self, timestamp, parentAddress, stationAddress, destinationStationAddress):
        self.timestamp = str(timestamp)
        self.parentAddress = str(parentAddress)
        self.stationAddress = str(stationAddress)
        self.destinationStationAddress = str(destinationStationAddress)

    def __str__(self):
        return f'{{ "timestamp" : {self.timestamp}, \
                    "parentAddress" : {self.parentAddress}, \
                    "stationAddress" : {self.stationAddress}, \
                    "destinationStationAddress" : {self.destinationStationAddress} \
            }}'


class MessageSentLogs:
    def __init__(self):
        self.logs = []

    def addLog(self, log):
        self.logs.append(log)

    def removeLog(self, destinationAddress, timestamp):
        for log in self.logs:
            if log.destinationAddress == str(destinationAddress) and log.timestamp == str(timestamp):
                self.logs.remove(log)


class Message:
    def __init__(self, sourceName, destinationName, tripType, time, timestamp):
        self.sourceName = '"' + sourceName + '"'
        if destinationName == None:
            destinationName = '""'
        else:
            destinationName = '"' + destinationName + '"'
        self.destinationName = destinationName
        self.route = []
        if tripType == None:
            tripType = '""'
        else:
            tripType = '"' + tripType + '"'
        self.tripType = tripType
        self.hopCount = 1  # set hop count to 1 initially
        self.time = time
        self.timestamp = timestamp

    def addRoute(self, station):
        stationString = station.getStationString(self.timestamp, self.time)
        self.route.append(stationString)

    def getRouteString(self):
        string = "["
        for item in self.route:
            string += str(item) + ", "
        string = string + "]"
        return string

    def __str__(self):
        return f'{{ "sourceName" : {self.sourceName} , \
                    "destinationName" : {self.destinationName} , \
                    "route": {self.getRouteString()}, \
                    "tripType": {self.tripType}, \
                    "hopCount": {self.hopCount} \
             }}'


html_content = """
<!DOCTYPE html>
<html>
    <head>
        <meta charset="utf-8"/>
        <title>Transperth Journey Planner</title>
        <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.5.1/jquery.min.js"></script>
        <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.4.1/css/bootstrap.min.css" integrity="sha384-Vkoo8x4CGsO3+Hhxv8T/Q5PaXtkKtu6ug5TOeNV6gBiFeWPGFN9MuhOf23Q9Ifjh" crossorigin="anonymous">
    </head>
    <body>
        <div class="container">
            <h1>Welcome to {station}</h1><br>
            Hello {address} <br>
            <form action="{stationTcpAddress}" method="GET">
                <div>
                    <label for="station">What station would you like to go to?</label>
                    <input name="station" id="station" class="form-control">
                </div>
                <div>
                    <label for="time">When do you want to leave?</label>
                    <select name="time" id="timetable" class="form-control"></select>
                </div>
                <div>
                    <label for="tripType">What type of trip?</label>
                    <select name="tripType" id="tripType" class="form-control"></select>
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
    const tripTypes = {tripTypes};

    const updateTimetable = ($timetable) => {{
        timetable.map(record => $('<option>')
            .attr({{ value : record[0] }})
            .text(record[0])
        ).forEach($option => $timetable.append($option));
    }}

    const updateTripType = ($tripType) => {{
        tripTypes.map(record => $('<option>')
            .attr({{ value : record }})
            .text(record)
        ).forEach($option => $tripType.append($option));
    }}

    $(() => {{
        const $timetable = $("#timetable");
        const $tripType = $("#tripType");
        updateTimetable($timetable);
        updateTripType($tripType);
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
    return str(request_array[0]).split(" ")[1].replace("/?", "")


def getRequestObject(request_body):
    request_body_objects = []
    request_body = request_body.split("&")
    for item in request_body:
        pair = item.split("=")
        request_body_objects.append({pair[0]: pair[1]})
    print(f"Request object: {request_body_objects}")
    return request_body_objects


def send_udp(key, mask, sel, station, requestObject, udpServerSocket, messageSentLogs):
    neighbours = station.neighbours
    timestamp = ts.time()
    msg = get_message_to_send(requestObject, station, timestamp)
    print(f"Message to send: {msg}")
    # msg = json.dumps(msg)
    msg_clean = str(msg).replace("'", '"')
    message = msg_clean.encode(FORMAT)
    msg_length = len(message)
    send_length = str(msg_length).encode(FORMAT)
    send_length += b" " * (station.HeaderSize - len(send_length))

    # send to each neighbour
    for neighbour in neighbours:
        newLog = MessageSentLog(
            timestamp, "", station.getStationUDPAddress(), neighbour.getStationUDPAddress())
        messageSentLogs.addLog(newLog)
        print(f"neighbour: {neighbour.udp_address}")
        udpServerSocket.sendto(send_length, neighbour.udp_address)
        udpServerSocket.sendto(message, neighbour.udp_address)

    for index, log in enumerate(messageSentLogs.logs):
        print(f"Log index: {index} || {str(log)}")


def get_message_to_send(requestObject, station, timestamp):
    destination = ""
    time = ""
    tripType = ""
    for item in requestObject:
        if item.get("station") != None:
            destination = item.get("station")
        if item.get("time") != None:
            time = str(item.get("time"))
            time = urllib.parse.unquote(time)
        if item.get("tripType") != None:
            tripType = item.get("tripType")
    message = Message(station.stationName,
                      destination,
                      tripType,
                      time,
                      timestamp)
    message.addRoute(station)
    return message


def service_tcp_connection(key, mask, sel, station, udpServerSocket, messageSentLogs):
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
            if "station" in requestBody:
                # send message
                requestObject = getRequestObject(requestBody)
                send_udp(key, mask, sel, station,
                         requestObject, udpServerSocket, messageSentLogs)

        else:  # the client has closed their socket so the server should too.
            print('closing connection to', data.addr)
            sel.unregister(sock)
            sock.close()
    if mask & selectors.EVENT_WRITE:  # write the data back to the client
        # we have received, and now we can send
        if request:
            sendData = "HTTP/1.1 200 OK\r\n"
            sendData += "Content-Type: text/html; charset=utf-8\r\n"
            sendData += "\r\n"
            sendData += html_content.format(station=station.stationName,
                                            timetable=station.timetable,
                                            address=data.addr,
                                            stationTcpAddress=station.getStationTCPAddress(),
                                            tripTypes=TRIP_TYPE)
            sock.send(sendData.encode())
            request = False  # request fulfiled
            sel.unregister(sock)
            sock.close()


def startTcpPort(station, sel):
    # create TCP server socket
    tcpServerSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcpServerSocket.bind(station.tcp_address)
    tcpServerSocket.listen()
    print(f"[LISTENING] TCP Server is listening on {station.tcp_address}.")
    tcpServerSocket.setblocking(False)
    sel.register(tcpServerSocket, selectors.EVENT_READ, data=None)
    return tcpServerSocket


def startUdpPort(station, sel):
    # create UDP server socket
    udpServerSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udpServerSocket.bind(station.udp_address)
    print(f"[LISTENING] UDP Server is listening on {station.udp_address}.")
    sel.register(udpServerSocket, selectors.EVENT_READ, data=None)
    return udpServerSocket


def serviceUdpCommunication(key, mask, sel, station, udpServerSocket, messageSentLogs):
    bytesAddressPair = udpServerSocket.recvfrom(
        station.HeaderSize)
    message_length = bytesAddressPair[0].decode()
    bytesAddressPair = udpServerSocket.recvfrom(
        int(message_length))
    print(f"Message length: {message_length}")
    message = bytesAddressPair[0].decode()
    message = eval(message)  # convert string to json
    address = bytesAddressPair[1]
    clientMsg = f"Message from Client:{message}"
    clientIP = f"Client IP Address:{address}"
    print(clientMsg)
    print(clientIP)

    print(f"sourceName: {message.get('sourceName')}")
    #         # udpServerSocket.sendto(
    #         #     "Hello from server.".encode(), address)


def serveTcpUdpPort(station, sel, tcpServerSocket, udpServerSocket, messageSentLogs):
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
                    if key.fileobj.getsockname() == station.tcp_address:
                        # print("TCP accept wrapper!")
                        accept_tcp_wrapper(key.fileobj, sel)

                    # if the listening socket is UDP
                    if key.fileobj.getsockname() == station.udp_address:
                        serviceUdpCommunication(
                            key, mask, sel, station, udpServerSocket, messageSentLogs)

                # a client socket that has been accepted and now we need to service it i.e. has data
                else:
                    if key.fileobj.getsockname() == station.tcp_address:
                        # print("TCP service connection!")
                        service_tcp_connection(
                            key, mask, sel, station, udpServerSocket, messageSentLogs)

            # conn, addr = tcpServerSocket.accept()  # accept new connection
            # handleTcpClient(station, conn, addr)
    except KeyboardInterrupt:
        print("Caught keyboard interrupt, exiting")
    finally:
        sel.close()


def acceptInputs(argv):
    if len(argv) == 0:
        print("Missing inputs.")
        sys.exit(2)

    stationName = argv[0]
    stationTcpPort = argv[1]  # e.g. tcp_port = 5050
    stationUdpPort = argv[2]  # e.g. udp_port = 6060

    station = Station(stationName, stationTcpPort, stationUdpPort)
    # create neighbour stations
    neighbourStationsUDP = argv[3:]
    for neighbourStationUDP in neighbourStationsUDP:
        neighbourStation = Station("", None, neighbourStationUDP)
        station.addNeighbour(neighbourStation)

    return station


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
    station = acceptInputs(argv)
    print(f"Station Name: {station.stationName}")
    print(f"tcp_address: {station.tcp_address}")
    print(f"udp_address: {station.udp_address}")
    print(f"Neighbour station: {station.neighbours}")

    # Read CSV timetable file -- assume that all contents are correct
    path = str(pathlib.Path(__file__).parent.absolute()).replace(
        "\src\pyStation", f"\datafiles\\tt-{station.stationName}")
    print(path)
    timetable, stationCoordinates = read_timetable(path)
    station.addCoordinates(
        float(stationCoordinates[1]), float(stationCoordinates[2]))  # add coordinates
    print(f"X: {station.x} | Y : {station.y} ")
    station.addTimetable(timetable)
    print("timetable: ")
    svrTimetable = station.timetable
    for row in svrTimetable:
        print(row)
    # Create selector
    sel = selectors.DefaultSelector()
    # Start TCP port
    tcpServerSocket = startTcpPort(station, sel)
    # Start UDP port
    udpServerSocket = startUdpPort(station, sel)
    # create new message sent logs object to hold messages sent from the server
    messageSentLogs = MessageSentLogs()
    # Serve TCP and UDP ports
    serveTcpUdpPort(station, sel, tcpServerSocket,
                    udpServerSocket, messageSentLogs)
    # TODO: Design and implementation of a simple programming language independent protocol to exchange queries,
    # responses, and (possibly) control information between stations.
    # TODO: Ability to find a valid (but not necessarily optimal) route between origin and destination stations,
    # for varying sized transport-networks of 2, 3, 5, 10, and 20 stations (including transport-networks involving cycles),
    # with no station attempting to collate information about the whole transport-network; ability to support multiple, concurrent queries from different clients.
    # TODO: Ability to detect and report when a valid route does not exist (on the current day).
    # TODO: look into JSON encoding issue: https://stackoverflow.com/questions/5160077/encoding-nested-python-object-in-json
    # TODO: check if timetable file has updated using stat()
    # TODO: Remove instant transit

    return None


if __name__ == "__main__":
    main(sys.argv[1:])
