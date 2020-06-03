import socket
import selectors
import types
import os
import sys
import csv
import pathlib
import json
import time as ts
import urllib
from datetime import datetime
import copy
import uuid

# CONSTANTS
SERVER = "127.0.0.1"
FORMAT = "UTF-8"
TRIP_TYPE = ["FastestTrip"]
MESSAGE_SIZE = 15000


class Station:
    def __init__(self, station, tcp_port, udp_port):
        self.stationName = station
        self.MessageSize = MESSAGE_SIZE
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

    def setCoordinates(self, x, y):
        self.x = x
        self.y = y

    def setTimetable(self, timetable):
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

    def getStationObject(self, messageId, time):
        return {
            "stationName": self.stationName,
            "messageId": messageId,
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
        removedLogs = []
        for log in self.logs:
            if log.msg["sourceName"] == msg["sourceName"] and log.msg["destinationName"] == msg["destinationName"] and log.msg["messageId"] == msg["messageId"]:
                removedLogs.append(log)
        for removedLog in removedLogs:
            self.logs.remove(removedLog)
        return removedLogs

    def getLog(self, msg):
        for log in self.logs:
            if log.msg["sourceName"] == msg["sourceName"] and log.msg["destinationName"] == msg["destinationName"] and log.msg["messageId"] == msg["messageId"]:
                return log


class MessageSentLog:
    def __init__(self, messageId, parentAddress, stationAddress, destinationStationAddress):
        self.messageId = str(messageId)
        self.parentAddress = str(parentAddress)
        self.stationAddress = str(stationAddress)
        self.destinationStationAddress = str(destinationStationAddress)


class MessageSentLogs:
    def __init__(self):
        self.logs = []

    def addLog(self, log):
        self.logs.append(log)

    def removeLog(self, parentAddress, destinationStationAddress, messageId):
        for record in self.logs:
            if str(record.parentAddress) == str(parentAddress) and str(record.destinationStationAddress) == str(destinationStationAddress) and str(record.messageId) == str(messageId):
                self.logs.remove(record)
                return record
        return None

    def getLogs(self, messageId):
        foundLog = []
        for record in self.logs:
            if str(record.messageId) == str(messageId):
                foundLog.append(record)
        if len(foundLog) > 0:
            return foundLog
        else:
            return None


class Message:
    def __init__(self, sourceName, destinationName, tripType, time, messageId, messageType):
        self.sourceName = sourceName
        self.destinationName = destinationName
        self.route = []
        self.tripType = tripType
        self.hopCount = 0  # set hop count to 0 initially
        self.time = time
        self.messageId = messageId
        self.messageType = messageType
        self.routeEndFound = False

    def addRoute(self, station):
        stationObject = station.getStationObject(self.messageId, self.time)
        self.route.append(stationObject)


class MessageBank:
    def __init__(self):
        self.bank = []

    def addMessage(self, message):
        self.bank.append(message)

    def removeMessage(self, hopCount, messageId):
        removedMessages = []
        print(f"Message Id to remove: {messageId}")
        for message in self.bank:
            # message["sourceName"] == sourceName and message["destinationName"] == destinationName and
            try:
                if message["route"][hopCount]["messageId"] == messageId:
                    removedMessages.append(message)
            except:
                pass  # the message is some other message that doesn't have the same hopCount

        for removedMessage in removedMessages:
            self.bank.remove(removedMessage)
            print(f"Removed message: {removedMessage}")

        return removedMessages


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
    console.log(stationResponse);
    const responses = {responses};
    const routeEndFound = {routeEndFound};
    console.log(routeEndFound);

    const respond = (response, $response, $responseList, routeEndFound) => {{
        $response.show();
        if(routeEndFound){{
            $responseList.append(
                `<li class="list-group-item">Oh uh! No route found!</li>`
            );
        }} else {{
            responses.forEach( (response, index) => {{
                list = `<li class="list-group-item">
                            <span class="badge badge-secondary badge-pill"> ${{index+1}}</span>
                            Depart from <b>${{response[0]}}</b> (<b>${{response[3]}}</b>) at <b>${{response[1]}}</b> taking <b>${{response[2]}}</b> and arrive at
                            <b>${{response[5]}}</b> at <b>${{response[4]}}</b>.
                        </li>`
                $responseList.append(list);
            }});
        }}
        
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
            respond(responses, $response, $responseList, routeEndFound);
        }}
    }});
</script>
"""


def acceptTcpWrapper(sock, sel):
    conn, addr = sock.accept()  # Should be ready to read
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
    return request_body_objects


def sendUdp(station, msg, udpServerSocket, messageSentLogs):
    neighbours = station.neighbours
    msg_clean = json.dumps(msg)
    message = msg_clean.encode(FORMAT)
    sentToNeighbours = 0
    # print(f"Station: {station.stationName} | my neighbours are:\n")
    # send to each neighbour
    for neighbour in neighbours:
        # Set send to true initially
        send = True
        # Don't send message to stations already in message
        for route in msg["route"]:
            if str(route["stationUDPAddress"]) == str(neighbour.getStationUDPAddress()):
                send = False
        # Don't send message to stations that a messageId already exists in the messageSentLogs (already sent to the neighbour)
        for index, log in enumerate(messageSentLogs.logs):
            if str(msg["messageId"]) == str(log.messageId) and str(neighbour.getStationUDPAddress()) == str(log.destinationStationAddress):
                send = False
        if send:
            # hopCount == 0 means that this is the source, so no parentAddress
            if msg["hopCount"] == 0:
                # MessageId, parent, station, destination
                newLog = MessageSentLog(
                    msg["route"][msg["hopCount"]]["messageId"], "", station.getStationUDPAddress(), neighbour.getStationUDPAddress())
            else:
                # use the parent stationUdpAddress
                newLog = MessageSentLog(
                    msg["route"][msg["hopCount"]]["messageId"], msg["route"][msg["hopCount"]-1]["stationUDPAddress"], station.getStationUDPAddress(), neighbour.getStationUDPAddress())
            messageSentLogs.addLog(newLog)
            udpServerSocket.sendto(message, neighbour.udp_address)
            sentToNeighbours = sentToNeighbours + 1
            print(
                f"Station: {station.stationName} || sending message to: {neighbour.udp_address}")
        else:
            print(f"Do not send message to {neighbour.udp_address}!")
    if sentToNeighbours == 0:
        return False  # did not send any udp datagram to neighbours
    else:
        return True  # sent at least one udp datagram to neighbour


def getMessageToSend(requestObject, station, messageId):
    destination = ""
    time = ""
    tripType = ""
    messageType = "outgoing"  # either outgoing or incoming
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
                      messageId,
                      messageType)
    message.addRoute(station)
    message = json.dumps(vars(message))  # return json object
    message = json.loads(message)
    return message


def findDestination(station, msg):
    destinationName = msg["destinationName"]
    route = msg["route"][msg["hopCount"]]
    for trip in msg["route"][msg["hopCount"]]["earliestTrips"]:
        if trip[4] == destinationName:
            return True, trip
    return False, []


def sendUdpToParent(station, msg, udpServerSocket, hopCountDeduct):
    # print(f"Entering sendUdpToParent function")
    msg["messageType"] = "incoming"
    msg["hopCount"] = msg["hopCount"] - hopCountDeduct
    # print(f"Dirty message at {station.stationName}: {msg}")
    msg_clean = json.dumps(msg)
    # print(f"Clean message at {station.stationName}: {msg_clean}")
    message = msg_clean.encode(FORMAT)

    # get parent object from the route
    parent = msg["route"][msg["hopCount"]]
    # send to parent
    addressList = parent["stationUDPAddress"].strip("http://").split(":")
    addressTuple = (addressList[0], int(addressList[1]))
    udpServerSocket.sendto(message, addressTuple)
    print(f"Incoming Message sent to parent: {addressTuple}")


def sendResponseToClient(station, data, earliestTrip, sock, sel, stationResponse, routeEndFound):
    if routeEndFound == True:
        routeEndFound = "true"
    else:
        routeEndFound = "false"
    sendData = "HTTP/1.1 200 OK\r\n"
    sendData += "Content-Type: text/html; charset=utf-8\r\n"
    sendData += "\r\n"
    sendData += html_content.format(station=station.stationName,
                                    timetable=station.timetable,
                                    address=data.addr,
                                    stationTcpAddress=station.getStationTCPAddress(),
                                    tripTypes=TRIP_TYPE,
                                    stationResponse=stationResponse,
                                    responses=earliestTrip,
                                    routeEndFound=routeEndFound)
    sock.send(sendData.encode())
    sel.unregister(sock)
    sock.close()
    return False


def incrementMessageId(MessageID):
    MessageID = MessageID + 1
    return MessageID


def serviceTcpConnection(key, mask, sel, station, udpServerSocket, messageSentLogs, clientRequestLogs, MessageID):
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
            requestBody = getRequestBody(recv_data.split("\r\n"))
            if "station" in requestBody:
                # Request has been received!
                requestObject = getRequestObject(requestBody)
                # Create message
                messageId = uuid.uuid1().int
                print(
                    f"StationName: {station.stationName} || Message ID: {messageId}")
                # get message to send and append station to message route and set hopCount to 0
                msg = getMessageToSend(requestObject, station, messageId)
                clientRequestLog = ClientRequestLog(
                    msg, sock, sel, data)
                clientRequestLogs.addLog(clientRequestLog)
                destFound, earliestTrip = findDestination(station, msg)
                if destFound:
                    # if destination is found, then send message back to client
                    earliestTrip.insert(0, station.stationName)
                    request = sendResponseToClient(
                        station, data, [earliestTrip], sock, sel, "true", False)
                    clientRequestLogs.removeLog(msg)
                if not destFound:
                    # if destination is not found, then pass message forward to other nodes
                    print(
                        f"Station: {station.stationName}. Servicing TCP Request. Sending UDP.")
                    sendUdp(station, msg,
                            udpServerSocket, messageSentLogs)

        else:  # the client has closed their socket so the server should too.
            print('closing connection to', data.addr)
            sel.unregister(sock)
            sock.close()
    if mask & selectors.EVENT_WRITE:  # write the data back to the client
        # we have received, and now we can send
        if request:
            send = True
            for log in clientRequestLogs.logs:
                if log.sock == sock:
                    send = False
            if send:
                request = sendResponseToClient(
                    station, data, [[]], sock, sel, "false", False)


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
    # udpServerSocket.setblocking(False)
    sel.register(udpServerSocket, selectors.EVENT_READ, data=None)
    return udpServerSocket


def removeNonDestination(message, station):
    newEarliestTrips = []
    destination = message["destinationName"]
    earliestTrips = message["route"][message["hopCount"]]["earliestTrips"]
    # create new list and add match to new list and replace old list
    for trip in earliestTrips:
        if trip[4] == destination:
            newEarliestTrips.append(trip)
    message["route"][message["hopCount"]]["earliestTrips"] = newEarliestTrips
    return message


def addStationToRoute(message, station, messageId):
    for trip in message["route"][message["hopCount"]]["earliestTrips"]:
        if trip[4] == station.stationName:
            lastRouteTime = trip[3]
    stationObject = station.getStationObject(messageId, lastRouteTime)
    message["route"].append(stationObject)
    message["hopCount"] = message["hopCount"] + 1
    return message


def collateMessages(msg, messageBank):
    """
    Obtain the earliest trip if there is a valid route. Remove messages from the messageBank with the matching messageId. 
    Else return the original message but set routeEndFound = True (in case). 
    """
    earliestMessage = None
    tripType = msg["tripType"]
    hopCount = msg["hopCount"]
    messageId = msg["route"][hopCount]["messageId"]

    if tripType == "FastestTrip":
        # just grab one record to set as the initial earliest time
        for message in messageBank.bank:
            try:
                if message["routeEndFound"] == False and message["route"][hopCount]["messageId"] == messageId:
                    # grab last route
                    earliestTime = message["route"][-1]["earliestTrips"][0][4]
                    earliestMessage = message
                    break
            except:
                pass  # the message is some other message that doesn't have the same hopCount
        # always grab the latest one (to destination) if looking for fastests trip
        for message in messageBank.bank:
            try:
                if message["routeEndFound"] == False and \
                    len(message["route"][-1]["earliestTrips"]) > 0 and \
                        message["route"][hopCount]["messageId"] == messageId:
                    # grab last route
                    compareEarliestTime = message["route"][-1]["earliestTrips"][0][4]
                    if compareEarliestTime < earliestTime:
                        earliestTime = compareEarliestTime
                        earliestMessage = message
            except:
                pass  # the message is some other message that doesn't have the same hopCount

        print(
            f'Removing message id from messageBank: {messageId}')
        # Remove all messages from the messageBank with the matching message id
        messageBank.removeMessage(hopCount, messageId)

        # if earliestMessage contains an object, then return the earliestMessage. Else return the original message but set routeEndFound = True.
        if earliestMessage != None:
            return earliestMessage
        else:
            msg["routeEndFound"] = True
            msg["messageType"] = "incoming"
            return msg


def removeVisitedFromEarliestTrips(msg):
    visited = []
    clonedMsg = copy.deepcopy(msg)

    for trip in clonedMsg["route"][clonedMsg["hopCount"]]["earliestTrips"]:
        for route in clonedMsg["route"]:
            if trip[4] == route["stationName"]:
                visited.append(trip)

    for visit in visited:
        clonedMsg["route"][clonedMsg["hopCount"]
                           ]["earliestTrips"].remove(visit)

    return clonedMsg


def routeEnd(station, msg):
    """
    Determine if there is a dead-end. 
    """
    visited = []
    routes = msg["route"]
    rmvedMsgs = removeVisitedFromEarliestTrips(msg)

    # if there's no earliest trip from the station, then no route is found
    if len(rmvedMsgs["route"][rmvedMsgs["hopCount"]]["earliestTrips"]) == 0:
        return True

    for neighbour in station.neighbours:
        visit = False
        for route in routes:
            if str(route["stationUDPAddress"]) == str(neighbour.getStationUDPAddress()):
                visit = True
                break
        visited.append(visit)  # mark this neighbour as visited

    for visit in visited:
        # if at least one more neighbour not yet visited then not dead end
        if visit == False:
            return False
    # else it is a dead end
    return True


def checkStationInEarliestTrips(msg, station):
    for trip in msg["route"][msg["hopCount"]]["earliestTrips"]:
        if trip[4] == station.stationName:
            return True  # yes this message was intended for me
    return False  # no this message was not intended for me


def findRoutePosition(route, stationName):
    for index, stop in enumerate(route):
        if stop["stationName"] == stationName:
            return index


def serviceUdpCommunication(key, mask, sel, station, udpServerSocket, messageSentLogs, clientRequestLogs, messageBank, MessageID):
    bytesAddressPair = udpServerSocket.recvfrom(
        station.MessageSize)
    message = bytesAddressPair[0].decode()
    msg = json.loads(message)  # load msg
    address = bytesAddressPair[1]
    destinationMsg = f"Message from Client:{message}"
    destinationIP = f"Destination IP Address:{address}"
    print(f"\n\nMessage received from {address}")
    print(f"Message from {address}: {message}")
    # message is incoming
    if msg["messageType"] == "incoming":
        print(f"Message type: incoming")
        # print(f"message received:{message}")
        # print(f"Source Station(message): {msg['sourceName']}")
        # print(f"Current station: {station.stationName}")
        # check if I am the source
        if msg["sourceName"] == station.stationName:
            # add message to message bank and remove from MessageSentLog
            print("message received!. i am the source.")
            messageBank.addMessage(msg)
            destinationStationAddress = f"http://{address[0]}:{address[1]}"
            removeMessageId = msg["route"][msg["hopCount"]]["messageId"]
            parentAddress = ""  # no parent address as this is the source
            print(
                f"attempting to remove messageId: {removeMessageId} || parentAddress: {parentAddress} || destinationStationAddress: {destinationStationAddress}")
            removedLog = messageSentLogs.removeLog(
                parentAddress, destinationStationAddress, removeMessageId)
            if removedLog == None:
                print(
                    f"Attempting to remove from message sent logs:")
                for index, log in enumerate(messageSentLogs.logs):
                    print(
                        f"index: {index} || log: {vars(log)}")
                print("\n")

                raise Exception(
                    f"@@@@@@@@ SOURCE @@@@@@@@@ Failed to remove messageId: {removeMessageId} || parentAddress: {parentAddress} || destinationStationAddress: {destinationStationAddress}")
            print(f"Removal successful.")

            if messageSentLogs.getLogs(removedLog.messageId) == None:
                # return webpage with trip details
                collatedMessage = collateMessages(msg, messageBank)

                print("It's for me!")
                earliestTrips = []
                routeEndFound = collatedMessage["routeEndFound"]
                if routeEndFound == False:
                    for route in collatedMessage["route"]:
                        route["earliestTrips"][0].insert(0,
                                                         route["stationName"])
                        earliestTrips.append(route["earliestTrips"][0])
                clientLog = clientRequestLogs.getLog(
                    collatedMessage)
                sendResponseToClient(
                    station, clientLog.data, earliestTrips, clientLog.sock, clientLog.sel, "true", routeEndFound)
                removedClientLogs = clientRequestLogs.removeLog(
                    collatedMessage)
        else:
            # add message to message bank and remove from MessageSentLog
            messageBank.addMessage(msg)
            destinationStationAddress = f"http://{address[0]}:{address[1]}"
            removeMessageId = msg["route"][msg["hopCount"]]["messageId"]
            parentAddress = msg["route"][findRoutePosition(
                msg["route"], station.stationName) - 1]["stationUDPAddress"]
            print(
                f"attempting to remove messageId: {removeMessageId} || parentAddress: {parentAddress} || destinationStationAddress: {destinationStationAddress}")
            removedLog = messageSentLogs.removeLog(
                parentAddress, destinationStationAddress, removeMessageId)
            if removedLog == None:
                print(
                    f"Attempting to remove from message sent logs:")
                for index, log in enumerate(messageSentLogs.logs):
                    print(
                        f"index: {index} || log: {vars(log)}")
                print("\n")
                raise Exception(
                    f"@@@@@@@ STATION @@@@@@@ Failed to remove messageId: {removeMessageId} || parentAddress: {parentAddress} || destinationStationAddress: {destinationStationAddress} \
                        from {' '.join(map(str,messageSentLogs.logs))}")
            print(f"Removal successful.")
            # print(
            #     f"station: {station.stationName} || Removed Log: {vars(removedLog)}")
            # if messageSentLog for message is empty, then collate messages from message bank and send back to parent
            if messageSentLogs.getLogs(removedLog.messageId) == None:
                # print("That's all folks!")
                print("Begin sending message back to parent.")
                collatedMessage = collateMessages(msg, messageBank)
                # for index, message in enumerate(messageBank.bank):
                #     print(
                #         f"Station: {station.stationName} || Message Bank Index:{index} || Message: {message} ")
                # print("Calling send udp parent function")
                sendUdpToParent(station, collatedMessage,
                                udpServerSocket, 1)  # pass it back to the parent an decrement the hopCount
                print(
                    f"station: {station.stationName} || Message sent to parent successfully. now awaiting the following other messages:")
                for index, log in enumerate(messageSentLogs.logs):
                    print(
                        f"station: {station.stationName} || index: {index} || log: {vars(log)}")
                print("\n")
            else:
                print(
                    f"Message removed. Waiting on other messages to return. Messages left:")
                for index, log in enumerate(messageSentLogs.getLogs(removedLog.messageId)):
                    print(
                        f"index: {index} || log: {vars(log)}")
                print("\n")

    # message is outgoing
    else:
        print(f"Message type: outgoing")
        if msg["destinationName"] == station.stationName:
            print(
                "dead end found! and I'm the destination. sending message back to parent.")
            msg["routeEndFound"] = True
            sendUdpToParent(station, msg, udpServerSocket, 0)
        else:
            messageIntended = checkStationInEarliestTrips(msg, station)
            print(f"This message was intended for me: {messageIntended}")
            # only perform actions if the message was intended for the station
            if messageIntended:
                # add station to route
                messageId = uuid.uuid1().int
                print(f"Generated message messageId: {messageId}")
                # Add station to route and increment hopCount + 1
                msg = addStationToRoute(msg, station, messageId)
                print(f"Added this station to the route")
                # check if destination is found
                destFound, earliestTrip = findDestination(station, msg)
                print(f"Destination has been found: {destFound}")
                if destFound:
                    print(f"<<<<<<<<<<<<< DESTINATION FOUND >>>>>>>>>>>>>>>>>")
                routeEndFound = routeEnd(station, msg)
                print(f"A dead end is detected: {routeEndFound}")
                # if station contains route to destination, then send back to source
                if destFound:
                    print("DestinationFound. Sending to parent.")
                    msg = removeNonDestination(msg, station)
                    sendUdpToParent(station, msg, udpServerSocket, 1)
                    parent = msg["route"][msg["hopCount"]]
                    print(f"message sent to parent. {parent}")
                # if station does not contain route to destination, then send to neighbours (outgoing)
                if destFound == False and routeEndFound == False:
                    sentToNeighbours = sendUdp(station, msg,
                                               udpServerSocket, messageSentLogs)
                    if sentToNeighbours == False:
                        # exhausted all means, send back to parent
                        msg["routeEndFound"] = True
                        sendUdpToParent(station, msg, udpServerSocket, 1)
                # found a dead end, send message back to parent
                if destFound == False and routeEndFound == True:
                    print("dead end found! sending back to parent")
                    msg["routeEndFound"] = True
                    sendUdpToParent(station, msg, udpServerSocket, 1)
            else:
                print("message was not intended for me! sending back to parent")
                msg["routeEndFound"] = True
                sendUdpToParent(station, msg, udpServerSocket, 0)


def readTimetable(filepath):
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


def checkAndUpdateTimetable(station, path, osstat):
    if osstat.st_mtime != os.stat(path).st_mtime:
        timetable, stationCoordinates = readTimetable(path)
        station.setTimetable(timetable)
        return os.stat(path)
    return osstat


def serveTcpUdpPort(station, sel, tcpServerSocket, udpServerSocket, messageSentLogs, clientRequestLogs, messageBank, path, osstat, MessageID):
    # wait for connection
    try:
        while True:
            # wait unitl registered file objects become ready and set a selector with no timeout
            # the call will block until file object becomes ready -- either TCP or UDP has an EVENT_READ
            events = sel.select(timeout=None)
            for key, mask in events:
                # check and update timetable each time a new event is triggered
                osstat = checkAndUpdateTimetable(station, path, osstat)
                # a listening socket that hasn't been accepted yet i.e. no data
                if key.data is None:

                    # if the listening socket is TCP
                    if key.fileobj.getsockname() == station.tcp_address:
                        acceptTcpWrapper(key.fileobj, sel)

                    # if the listening socket is UDP
                    if key.fileobj.getsockname() == station.udp_address:
                        serviceUdpCommunication(
                            key, mask, sel, station, udpServerSocket, messageSentLogs, clientRequestLogs, messageBank, MessageID)

                # a client socket that has been accepted and now we need to service it i.e. has data
                else:
                    try:
                        if key.fileobj.getsockname() == station.tcp_address:
                            serviceTcpConnection(
                                key, mask, sel, station, udpServerSocket, messageSentLogs, clientRequestLogs, MessageID)
                    except:
                        print("TCP Connetion is closed.")
                        pass

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


def main(argv):
    # store config and neighbours from inputs
    station = acceptInputs(argv)
    print(f"Station Name: {station.stationName}")
    print(f"tcp_address: {station.tcp_address}")
    print(f"udp_address: {station.udp_address}")
    print(f"Neighbour station: {station.neighbours}")

    # Read CSV timetable file -- assume that all contents are correct
    path = str(pathlib.Path(__file__).parent.absolute()) + \
        f"/tt-{station.stationName}"
    osstat = os.stat(path)
    print(osstat)
    timetable, stationCoordinates = readTimetable(path)
    station.setCoordinates(
        float(stationCoordinates[1]), float(stationCoordinates[2]))  # add coordinates
    print(f"X: {station.x} | Y : {station.y} ")
    station.setTimetable(timetable)
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
    messageBank = MessageBank()
    MessageID = 0
    # Serve TCP and UDP ports
    serveTcpUdpPort(station, sel, tcpServerSocket,
                    udpServerSocket, messageSentLogs, clientRequestLogs, messageBank, path, osstat, MessageID)

    # TODO: Ability to find a valid (but not necessarily optimal) route between origin and destination stations,
    # for varying sized transport-networks of 2, 3, 5, 10, and 20 stations (including transport-networks involving cycles),
    # with no station attempting to collate information about the whole transport-network; ability to support multiple, concurrent queries from different clients.
    # TODO: commenting, separating python files, throwing errors

    return None


if __name__ == "__main__":
    main(sys.argv[1:])
