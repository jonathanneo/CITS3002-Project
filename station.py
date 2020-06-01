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

    def getStationUDPAddress(self):
        return f"http://{self.server}:{self.udp_port}"

    def getStationTCPAddress(self):
        return f"http://{self.server}:{self.tcp_port}"

    def getEarliestTrips(self, time):
        earliestTrips = []
        for timetableRecord in self.timetable:
            timeValue = datetime.strptime(time, "%H:%M")
            timetableRecordTime = datetime.strptime(
                timetableRecord[0], "%H:%M")
            timetableRecordDestination = str(timetableRecord[4])
            if len(earliestTrips) == 0:
                if timetableRecordTime >= timeValue:
                    earliestTrips.append(
                        timetableRecord)
            else:
                recordFound = False
                for trips in earliestTrips:
                    if timetableRecordTime >= timeValue and str(trips[4]) == str(timetableRecordDestination):
                        recordFound = True
                if recordFound == False:
                    earliestTrips.append(
                        timetableRecord)
        return earliestTrips

    def getStationObject(self, timestamp, time):
        return {
            "stationName": self.stationName,
            "timestamp": timestamp,
            "stationUDPAddress": self.getStationUDPAddress(),
            "earliestTrips": self.getEarliestTrips(time)
        }


class ClientRequestLog:
    def __init__(self, msg, sock, sel, data):
        self.msg = msg
        self.sock = sock
        self.sel = sel
        self.data = data


class ClientRequestLogs:
    def __init__(self):
        self.logs = []

    def addLog(self, log):
        self.logs.append(log)

    def removeLog(self, msg):
        for log in self.logs:
            if log.msg["sourceName"] == msg["sourceName"] and log.msg["destinationName"] == msg["destinationName"] and log.msg["timestamp"] == msg["timestamp"]:
                self.logs.remove(log)

    def getLog(self, msg):
        for log in self.logs:
            if log.msg["sourceName"] == msg["sourceName"] and log.msg["destinationName"] == msg["destinationName"] and log.msg["timestamp"] == msg["timestamp"]:
                return log


class MessageSentLog:
    def __init__(self, timestamp, parentAddress, stationAddress, destinationStationAddress):
        self.timestamp = str(timestamp)
        self.parentAddress = str(parentAddress)
        self.stationAddress = str(stationAddress)
        self.destinationStationAddress = str(destinationStationAddress)


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
    def __init__(self, sourceName, destinationName, tripType, time, timestamp, messageType):
        self.sourceName = sourceName
        self.destinationName = destinationName
        self.route = []
        self.tripType = tripType
        self.hopCount = 0  # set hop count to 0 initially
        self.time = time
        self.timestamp = timestamp
        self.messageType = messageType

    def addRoute(self, station):
        stationObject = station.getStationObject(self.timestamp, self.time)
        self.route.append(stationObject)


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
                <br>
                <div>
                    <input type="submit" value="Get travel plan" class="btn btn-primary">
                </div>
            </form>

            <div id="response">
                <br>
                <hr>
                <h4>Trip Details</h4>
                <div class="card">
                    <ul id="response-list" class="list-group list-group-flush">
                    </ul>
                </div>
            </div>
        </div>
    </body>
</html>

<script type="text/javascript">

    const timetable = {timetable};
    const tripTypes = {tripTypes};
    const stationResponse = {stationResponse};
    const responses = {responses};

    const respond = (response, $response, $responseList) => {{
        $response.show();
        responses.forEach( (response, index) => {{
            list = `<li class="list-group-item">
                        <span class="badge badge-secondary badge-pill"> ${{index+1}}</span>
                        Depart at <b>${{response[0]}}</b> from <b>${{response[2]}}</b> taking <b>${{response[1]}}</b> and arrive at
                        <b>${{response[4]}}</b> at <b>${{response[3]}}</b>.
                    </li>`
            $responseList.append(list);
        }});
    }}

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
        const $response = $("#response")
        const $responseList = $("#response-list")
        $response.hide();
        updateTimetable($timetable);
        updateTripType($tripType);
        if(stationResponse){{
            respond(responses, $response, $responseList);
        }}
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


def send_udp(key, mask, sel, station, msg, udpServerSocket, messageSentLogs):
    neighbours = station.neighbours
    print(f"Message to send: {msg}")
    msg_clean = json.dumps(msg)
    message = msg_clean.encode(FORMAT)
    msg_length = len(message)
    send_length = str(msg_length).encode(FORMAT)
    send_length += b" " * (station.HeaderSize - len(send_length))

    # send to each neighbour
    for neighbour in neighbours:
        newLog = MessageSentLog(
            msg["timestamp"], "", station.getStationUDPAddress(), neighbour.getStationUDPAddress())
        messageSentLogs.addLog(newLog)
        print(f"neighbour: {neighbour.udp_address}")
        udpServerSocket.sendto(send_length, neighbour.udp_address)
        udpServerSocket.sendto(message, neighbour.udp_address)

    for index, log in enumerate(messageSentLogs.logs):
        print(f"Log index: {index} || {vars(log)}")


def get_message_to_send(requestObject, station, timestamp):
    destination = ""
    time = ""
    tripType = ""
    messageType = "outgoing"  # either outgoing or incoming
    print(f"REQUEST OBJECT : {requestObject}")
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
                      timestamp,
                      messageType)
    message.addRoute(station)
    print(vars(message))
    message = json.dumps(vars(message))  # return json object
    message = json.loads(message)
    return message


def findDestination(station, msg):
    destinationName = msg["destinationName"]
    route = msg["route"][msg["hopCount"]]
    print(f"route: {route}")
    for trip in msg["route"][msg["hopCount"]]["earliestTrips"]:
        if trip[4] == destinationName:
            print(trip)
            return True, trip
    return False, []


def send_udp_to_parent(key, mask, sel, station, msg, udpServerSocket, messageSentLogs):
    neighbours = station.neighbours
    print(f"Message to send: {msg}")
    msg["messageType"] = "incoming"
    msg["hopCount"] = msg["hopCount"] - 1
    msg_clean = json.dumps(msg)
    message = msg_clean.encode(FORMAT)
    msg_length = len(message)
    send_length = str(msg_length).encode(FORMAT)
    send_length += b" " * (station.HeaderSize - len(send_length))

    # get parent
    parent = msg["route"][msg["hopCount"]]
    print(parent)
    # send to parent
    addressList = parent["stationUDPAddress"].strip("http://").split(":")
    addressTuple = (addressList[0], int(addressList[1]))
    udpServerSocket.sendto(send_length, addressTuple)
    udpServerSocket.sendto(message, addressTuple)


def send_response_to_client(station, data, earliestTrip, sock, sel, stationResponse):
    sendData = "HTTP/1.1 200 OK\r\n"
    sendData += "Content-Type: text/html; charset=utf-8\r\n"
    sendData += "\r\n"
    sendData += html_content.format(station=station.stationName,
                                    timetable=station.timetable,
                                    address=data.addr,
                                    stationTcpAddress=station.getStationTCPAddress(),
                                    tripTypes=TRIP_TYPE,
                                    stationResponse=stationResponse,
                                    responses=[earliestTrip])
    sock.send(sendData.encode())
    sel.unregister(sock)
    sock.close()
    return False


def service_tcp_connection(key, mask, sel, station, udpServerSocket, messageSentLogs, clientRequestLogs):
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
                # Request has been received!
                requestObject = getRequestObject(requestBody)
                # Create message
                timestamp = ts.time()
                msg = get_message_to_send(requestObject, station, timestamp)
                clientRequestLog = ClientRequestLog(
                    msg, sock, sel, data)
                # print(f"CLIENT REQUEST LOG: {vars(clientRequestLog)}")
                clientRequestLogs.addLog(clientRequestLog)
                destFound, earliestTrip = findDestination(station, msg)
                if destFound:
                    # if server is the source server, then send message back to client
                    request = send_response_to_client(
                        station, data, earliestTrip, sock, sel, "true")
                    # clientRequestLogs.removeLog(msg)
                if not destFound:
                    # if destination is not found, then pass message forward to other nodes
                    send_udp(key, mask, sel, station, msg,
                             udpServerSocket, messageSentLogs)

        else:  # the client has closed their socket so the server should too.
            print('closing connection to', data.addr)
            sel.unregister(sock)
            sock.close()
    if mask & selectors.EVENT_WRITE:  # write the data back to the client
        # we have received, and now we can send
        if request:
            request = send_response_to_client(
                station, data, [], sock, sel, "false")


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


def remove_non_destination(message, station):
    newEarliestTrips = []
    destination = message["destinationName"]
    earliestTrips = message["route"][message["hopCount"]]["earliestTrips"]
    # create new list and add match to new list and replace old list
    for trip in earliestTrips:
        if trip[4] == destination:
            newEarliestTrips.append(trip)
    message["route"][message["hopCount"]]["earliestTrips"] = newEarliestTrips
    return message


def get_incoming_earliest_trip(message, station):
    return message


def add_station_to_route(message, station, timestamp):
    print(f"MESSAGE || : {message}")
    for trip in message["route"][message["hopCount"]]["earliestTrips"]:
        if trip[4] == station.stationName:
            lastRouteTime = trip[3]
    stationObject = station.getStationObject(timestamp, lastRouteTime)
    # print(f"station object: {stationObject}")
    message["route"].append(stationObject)
    message["hopCount"] = message["hopCount"] + 1
    return message


def serviceUdpCommunication(key, mask, sel, station, udpServerSocket, messageSentLogs, clientRequestLogs):
    bytesAddressPair = udpServerSocket.recvfrom(
        station.HeaderSize)
    message_length = bytesAddressPair[0].decode()
    bytesAddressPair = udpServerSocket.recvfrom(
        int(message_length))
    print(f"Message length: {message_length}")
    message = bytesAddressPair[0].decode()
    msg = json.loads(message)  # load msg
    address = bytesAddressPair[1]
    clientMsg = f"Message from Client:{message}"
    clientIP = f"Client IP Address:{address}"
    print(f"sourceName: {msg['sourceName']}")
    print(clientMsg)
    print(clientIP)

    # add message to waiting bay
    # if all messages has not returned, then do nothing
    # else , fetch from waiting bay and process all messages

    # check if I am the source
    if msg["messageType"] == "incoming" and msg["sourceName"] == station.stationName:
        # return webpage with trip details
        sock = key.fileobj
        data = key.data
        print("It's for me!")
        earliestTrips = []
        for route in msg["route"]:
            earliestTrips.append(route["earliestTrips"])
        clientLog = clientRequestLogs.getLog(
            msg)  # clientRequestLogs.logs[0]  #
        print(f"SOCK: {clientLog.sock}")
        print(f"DATA: {clientLog.data.addr}")
        # print(f"raddr: {clientLog.sock.socket.getpeername()}")
        # clientLog.sock.connect()
        # clientSocket = socket.create_connection(clientLog.data.addr)
        send_response_to_client(
            station, clientLog.data, earliestTrips, clientLog.sock, clientLog.sel, "true")
    else:
        # add station to route
        timestamp = ts.time()
        msg = add_station_to_route(msg, station, timestamp)
        # check if destination is found
        destFound, earliestTrip = findDestination(station, msg)
        print(destFound)
        print(earliestTrip)
        # if station contains route to destination, then send back to source (incoming)
        if destFound:
            msg = remove_non_destination(msg, station)
            send_udp_to_parent(key, mask, sel, station, msg,
                               udpServerSocket, messageSentLogs)
        # if station does not contain route to destination, then send to neighbours (outgoing)
        if not destFound:
            send_udp(key, mask, sel, station, msg,
                     udpServerSocket, messageSentLogs)
        #         # udpServerSocket.sendto(
        #         #     "Hello from server.".encode(), address)


def serveTcpUdpPort(station, sel, tcpServerSocket, udpServerSocket, messageSentLogs, clientRequestLogs):
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
                            key, mask, sel, station, udpServerSocket, messageSentLogs, clientRequestLogs)

                # a client socket that has been accepted and now we need to service it i.e. has data
                else:
                    if key.fileobj.getsockname() == station.tcp_address:
                        # print("TCP service connection!")
                        service_tcp_connection(
                            key, mask, sel, station, udpServerSocket, messageSentLogs, clientRequestLogs)

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
    path = str(pathlib.Path(__file__).parent.absolute()) + \
        f"\\tt-{station.stationName}"
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
    clientRequestLogs = ClientRequestLogs()
    # Serve TCP and UDP ports
    serveTcpUdpPort(station, sel, tcpServerSocket,
                    udpServerSocket, messageSentLogs, clientRequestLogs)
    # TODO: 1) Create the message when a new TCP client request is received
    # 2) check if destination matches the timetable records. If so, get the earliest time.
    # 3) if current station is the source, then respond back to client. Else if station is not source, then send message back to parent.
    # 4) if destination doesn't match, then forward on the message to neighbours (append station object to message route[]), but not to the parent.
    # TODO: if neighbour == destination, then use timing based on timetable
    # TODO: Design and implementation of a simple programming language independent protocol to exchange queries,
    # responses, and (possibly) control information between stations.
    # TODO: go to the edges and return "not found" if destination not found
    # TODO: create code to evaluate FastestTrip or LeastTransfers at each station
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
