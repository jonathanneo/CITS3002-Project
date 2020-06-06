import java.nio.channels.ServerSocketChannel;
import java.nio.channels.SocketChannel;
import java.nio.channels.Selector;
import java.nio.channels.DatagramChannel;
import java.nio.channels.SelectionKey;
import java.nio.ByteBuffer;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.UUID;
import java.io.*;
import java.net.InetSocketAddress;
import java.net.ServerSocket;
import java.net.SocketAddress;
import java.net.Socket;
import java.util.Iterator;
import java.util.Set;
import java.util.HashMap;
import com.google.gson.*;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.net.URLDecoder;

/**
 * @author Jonathan Neo
 */

public class Station {

    // CONSTANTS
    String SERVER = "127.0.0.1";
    String FORMAT = "UTF-8";
    String[] TRIP_TYPE = { "FastestTrip" };
    int MESSAGE_SIZE = 50000;

    // variables
    String stationName;
    int messageSize;
    int tcpPort;
    int udpPort;
    String format;
    String server;
    List<Station> neighbours;
    List<List<String>> timetable;

    public Station() {
        // empty constructor
    }

    /**
     * Constructor for Station
     * 
     * @param stationName
     * @param tcpPort
     * @param udpPort
     */
    public Station(String stationName, String tcpPort, String udpPort) {
        this.stationName = stationName;
        // tcp port may be empty if it is used as a neighbour
        try {
            this.tcpPort = Integer.parseInt(tcpPort);
        } catch (Exception e) {
            this.tcpPort = -1;
        }
        this.udpPort = Integer.parseInt(udpPort);
        this.server = this.SERVER;
        this.messageSize = this.MESSAGE_SIZE;
        this.format = this.FORMAT;
        this.neighbours = new ArrayList<Station>();
        this.timetable = new ArrayList<List<String>>();
    }

    public void setTimetable(List<List<String>> timetable) {
        this.timetable = timetable;
    }

    public void addNeighbour(Station neighbour) {
        this.neighbours.add(neighbour);
    }

    public String getStationUdpAddress() {
        return "http://" + this.server + ":" + Integer.toString(this.udpPort);
    }

    public String getStationTcpAddress() {
        return "http://" + this.server + ":" + Integer.toString(this.tcpPort);
    }

    public List<List<String>> getEarliestTrips(String time) throws Exception {
        List<List<String>> earliestTrips = new ArrayList<List<String>>();
        try {
            for (List<String> timetableRecord : this.timetable) {
                Date timeValue = new SimpleDateFormat("HH:mm").parse(time);
                Date timetableRecordTime = new SimpleDateFormat("HH:mm").parse(timetableRecord.get(0));

                String timetableRecordDestination = timetableRecord.get(4);
                // first trip
                if (earliestTrips.size() == 0) {
                    if (timetableRecordTime.compareTo(timeValue) >= 0) {
                        System.out.println("initial size of 0");
                        // System.out.println("Added timetableRecord: " + timetableRecord);
                        earliestTrips.add(timetableRecord);
                        // System.out.println("earliestTrips List: " + earliestTrips);
                    }
                } else {
                    Boolean recordFound = false;
                    for (List<String> trips : earliestTrips) {
                        // if already in earliestTrips then do not add
                        if ((timetableRecordTime.compareTo(timeValue) >= 0)
                                && (trips.get(4).equals(timetableRecordDestination))) {
                            recordFound = true;
                            break;
                        }
                    }
                    // if not yet in earliestTrips, then add
                    if (recordFound == false) {
                        earliestTrips.add(timetableRecord);
                    }
                }
            }
            Gson gson = new Gson();
            System.out.println("EarliestTrips: " + gson.toJson(earliestTrips));
            return earliestTrips;
        } catch (Exception e) {
            throw new Exception("Could not parse time correctly. Full error message: " + e);
        }
    }

    /**
     * Class to hold the station object
     */
    public class StationObject {
        String stationName;
        String messageId;
        String stationUDPAddress;
        List<List<String>> earliestTrips;

        /**
         * Constructor of the stationObject
         * 
         * @param stationName
         * @param messageId
         * @param stationUDPAddress
         * @param earliestTrips
         */
        public StationObject(String stationName, String messageId, String stationUDPAddress,
                List<List<String>> earliestTrips) {
            this.stationName = stationName;
            this.messageId = messageId;
            this.stationUDPAddress = stationUDPAddress;
            this.earliestTrips = earliestTrips;
        }
    }

    /**
     * Get the station object
     * 
     * @param messageId
     * @param time
     * @return StationObject
     * @throws Exception when (String) Time cannot be casted to (SimpleDateFormat)
     *                   Time
     */
    public StationObject getStationObject(String messageId, String time) throws Exception {
        StationObject obj = new StationObject(this.stationName, messageId, this.getStationUdpAddress(),
                this.getEarliestTrips(time));
        return obj;
    }

    /**
     * Subclass for ClientRequestLog which is used to stores the socket channel used
     * for communication with the client
     */
    public class ClientRequestLog {
        SocketChannel socketChannel;

        public ClientRequestLog() {
            // empty constructor
        }

        public void setSocketChannel(SocketChannel socketChannel) {
            this.socketChannel = socketChannel;
        }

        public SocketChannel getSocketChannel() {
            return this.socketChannel;
        }
    }

    /**
     * Subclass that stores the metadata of a message sent from the station
     */
    public class MessageSentLog {
        String messageId;
        String parentAddress;
        String stationAddress;
        String destinationStationAddress;

        /**
         * Constructor for the MessageSentLog
         * 
         * @param messageId
         * @param parentAddress
         * @param stationAddress
         * @param destinationStationAddress
         */
        public MessageSentLog(String messageId, String parentAddress, String stationAddress,
                String destinationStationAddress) {
            this.messageId = messageId;
            this.parentAddress = parentAddress;
            this.stationAddress = stationAddress;
            this.destinationStationAddress = destinationStationAddress;
        }
    }

    /**
     * Subclass that stores a list of MessageSentLog's sent from the station
     */
    public class MessageSentLogs {
        List<MessageSentLog> logs = new ArrayList<MessageSentLog>();

        /**
         * Method for adding log to messageSentLogs
         * 
         * @param log
         */
        public void addLog(MessageSentLog log) {
            logs.add(log);
        }

        /**
         * Remove the log from messageSentLogs
         * 
         * @param parentAddress
         * @param destinationStationAddress
         * @param messageId
         * @return
         */
        public MessageSentLog removeLog(String parentAddress, String destinationStationAddress, String messageId)
                throws Exception {
            List<MessageSentLog> logsToRemove = new ArrayList<MessageSentLog>();
            try {
                for (MessageSentLog log : this.logs) {
                    if (log.parentAddress.equals(parentAddress)
                            && log.destinationStationAddress.equals(destinationStationAddress)
                            && log.messageId.equals(messageId)) {
                        logsToRemove.add(log);
                    }
                }
            } catch (Exception e) {
                throw e;
            }

            Gson gson = new Gson();
            System.out.println("Logs to be removed list: " + gson.toJson(logsToRemove));

            for (MessageSentLog logToRemove : logsToRemove) {
                System.out.println("Log to be removed: " + gson.toJson(logToRemove));
                this.logs.remove(logToRemove);
                System.out.println("Removed log.");
                return logToRemove;
            }
            System.out.println("There was no log to remove.");
            return null;
        }

        /**
         * Return found MessageSentLogs that match the messageId
         * 
         * @param messageId
         * @return
         */
        public List<MessageSentLog> getLogs(String messageId) {
            List<MessageSentLog> foundLog = new ArrayList<MessageSentLog>();

            for (MessageSentLog log : this.logs) {
                if (log.messageId.equals(messageId)) {
                    foundLog.add(log);
                }
            }
            if (foundLog.size() > 0) {
                return foundLog;
            }
            return null;
        }
    }

    /**
     * Class used to store the message that will be communicated between stations
     * via UDP
     */
    public class Message {
        String sourceName;
        String destinationName;
        List<StationObject> route;
        String tripType;
        int hopCount;
        String time;
        String messageId;
        String messageType;
        Boolean routeEndFound;

        /**
         * Constructor for the message class
         * 
         * @param sourceName
         * @param destinationName
         * @param tripType
         * @param time
         * @param messageId
         * @param messageType
         */
        public Message(String sourceName, String destinationName, String tripType, String time, String messageId,
                String messageType) {
            this.sourceName = sourceName;
            this.destinationName = destinationName;
            this.route = new ArrayList<StationObject>();
            this.tripType = tripType;
            this.hopCount = 0; // set hopCount to 0 initially
            this.time = time;
            this.messageId = messageId;
            this.routeEndFound = false; // no dead end found
            this.messageType = messageType;
        }

        /**
         * Gets the stationJsonObject based on the station object and adds to route
         * 
         * @param station
         * @throws Exception when time cannot be casted to date
         */
        public void addRoute(Station station) throws Exception {
            StationObject stationObject = station.getStationObject(this.messageId, this.time);
            this.route.add(stationObject);
        }
    }

    /**
     * Used to store JSON messages received from neighbouring stations and store
     * here until can be collated and sent to parent
     */
    public class MessageBank {
        List<Message> bank = new ArrayList<Message>();

        /**
         * Add message to message bank
         * 
         * @param message
         */
        public void addMessage(Message message) {
            this.bank.add(message);
        }

        public List<Message> removeMessage(int hopCount, String messageId) {
            List<Message> removedMessages = new ArrayList<Message>();
            for (Message message : this.bank) {
                try {
                    List<StationObject> route = (List<StationObject>) message.route;
                    StationObject bankStation = (StationObject) route.get(hopCount);
                    String bankMessageId = (String) bankStation.messageId;
                    if (bankMessageId.equals(messageId)) {
                        removedMessages.add(message);
                    }
                } catch (Exception e) {
                    // do nothing. the message is some other message that doesn't have the same
                    // hopCount
                }
            }
            for (Message removedMessage : removedMessages) {
                this.bank.remove(removedMessage);
            }
            return removedMessages;
        }
    }

    /**
     * Get request body
     * 
     * @param requestArray
     * @return
     */
    public static String getRequestBody(String request) {
        try {
            List<String> requestArray = Arrays.asList(request.split("\r\n"));
            String requestString = requestArray.get(0);
            String[] requestStringList = requestString.split(" ");
            requestString = requestStringList[1];
            requestString = requestString.replace("/?", "");
            return requestString;
        } catch (Exception e) {
            // do nothing
        }
        return new String();
    }

    /**
     * Get an object pairing of request items
     * 
     * @param requestBody
     * @return
     */
    public static List<HashMap<String, String>> getRequestObject(String requestBody) {
        List<HashMap<String, String>> requestBodyObjects = new ArrayList<HashMap<String, String>>();
        String[] requestBodyList = requestBody.split("&");
        for (String item : requestBodyList) {
            String[] pair = item.split("=");
            HashMap<String, String> obj = new HashMap<String, String>();
            obj.put((String) pair[0], (String) pair[1]);
            requestBodyObjects.add(obj);
        }
        return requestBodyObjects;
    }

    /**
     * Keep only earliest trips that aren't duplicates
     * 
     * @param msg
     * @return msg containing earliest trips that aren't duplicates
     */
    public static Message matchRoute(Message msg) {
        List<StationObject> routes = msg.route;
        int numRoutes = routes.size();
        for (int index = 0; index < numRoutes; index++) {
            StationObject route = routes.get(index);
            List<List<String>> earliestTrips = route.earliestTrips;
            List<List<String>> removeTrip = new ArrayList<List<String>>();
            if (index + 1 < numRoutes) {
                for (List<String> trip : earliestTrips) {
                    StationObject nextRoute = (StationObject) routes.get(index + 1);
                    if (!trip.get(4).equals(nextRoute.stationName)) {
                        removeTrip.add(trip);
                    }
                }
            } else {
                for (List<String> trip : earliestTrips) {
                    if (!trip.get(4).equals(msg.destinationName)) {
                        removeTrip.add(trip);
                    }
                }
            }
            for (List<String> trip : removeTrip) {
                earliestTrips.remove(trip);
            }
        }
        return msg;
    }

    public static Message addRouteStationToTripDetails(Message msg) {
        for (StationObject route : msg.route) {
            List<List<String>> tempList = new ArrayList<List<String>>(route.earliestTrips);
            List<String> tempTempList = new ArrayList<String>(tempList.get(0));
            tempTempList.add(0, route.stationName);
            List<List<String>> emptyList = new ArrayList<List<String>>();
            emptyList.add(tempTempList);
            route.earliestTrips = emptyList;
        }
        return msg;
    }

    /**
     * 
     * @param requestObject
     * @param station
     * @param messageId
     * @return
     * @throws Exception when time cannot be casted
     */
    public Message getMessageToSend(List<HashMap<String, String>> requestObject, Station station, String messageId)
            throws Exception {
        String destination = "";
        String time = "";
        String tripType = "";
        String messageType = "outgoing";
        for (HashMap<String, String> item : requestObject) {
            if (item.get("to") != null) {
                destination = (String) item.get("to");
            }
            if (item.get("time") != null) {
                time = (String) item.get("time");
                // decode time
                try {
                    time = java.net.URLDecoder.decode(time, StandardCharsets.UTF_8.name());
                } catch (UnsupportedEncodingException e) {
                    // not going to happen - value came from JDK's own StandardCharsets
                }
            }
            if (item.get("tripType") != null) {
                tripType = (String) item.get("tripType");
            }
        }
        if (time.equals("")) {
            Date date = new Date();
            SimpleDateFormat formatter = new SimpleDateFormat("HH:mm");
            time = formatter.format(date);
        }
        if (tripType.equals("")) {
            tripType = "FastestTrip";
        }
        System.out.println(">>>>>>>>> Time: " + time);
        Message message = new Message(station.stationName, destination, tripType, time, messageId, messageType);
        message.addRoute(station);
        return message;
    }

    /**
     * Checks if the destination is within reach from the station
     * 
     * @param station
     * @param msg
     * @return List<Object> containing [Boolean, List<StationObject>]
     */
    public static List<Object> findDestination(Station station, Message msg) {
        List<Object> returnList = new ArrayList<Object>();
        String destinationName = msg.destinationName;
        List<StationObject> routes = msg.route;
        StationObject route = routes.get(msg.hopCount);
        for (List<String> trip : route.earliestTrips) {
            if (trip.get(4).equals(destinationName)) {
                returnList.add(true);
                returnList.add(trip);
            }
        }
        returnList.add(false);
        returnList.add(new ArrayList());
        return returnList;
    }

    public static String getSummarisedTrip(Message msg) {
        String sourceName = msg.sourceName;
        String destinationName = msg.destinationName;
        Gson gson = new Gson();

        List<String> sourceTrip = msg.route.get(0).earliestTrips.get(0);
        System.out.println("sourceTrip: " + gson.toJson(sourceTrip));
        List<String> destinationTrip = msg.route.get(msg.route.size() - 1).earliestTrips.get(0);
        String summarisedTrip = "Depart from " + sourceName + " (" + sourceTrip.get(3) + ") at " + sourceTrip.get(1)
                + " taking " + sourceTrip.get(2) + " and eventually arrive at " + destinationName + " at "
                + destinationTrip.get(4) + ". View trip details below.";
        return summarisedTrip;
    }

    public static Message removeNonDestination(Message message, Station station) {
        List<List<String>> newEarliestTrips = new ArrayList<List<String>>();
        String destination = message.destinationName;
        List<List<String>> earliestTrips = message.route.get(message.hopCount).earliestTrips;
        for (List<String> trip : earliestTrips) {
            if (trip.get(4).equals(destination)) {
                newEarliestTrips.add(trip);
            }
        }
        message.route.get(message.hopCount).earliestTrips = newEarliestTrips;
        return message;
    }

    /**
     * Add a station to the message's route
     * 
     * @param message
     * @param station
     * @param messageId
     * @return
     * @throws Exception when time (string) cannot be casted to time (date)
     */
    public static Message addStationToRoute(Message message, Station station, String messageId) throws Exception {
        String lastRouteTime = "";
        for (List<String> trip : message.route.get(message.hopCount).earliestTrips) {
            if (trip.get(4).equals(station.stationName)) {
                lastRouteTime = trip.get(3);
            }
        }
        StationObject stationObject = station.getStationObject(messageId, lastRouteTime);
        message.route.add(stationObject);
        message.hopCount++;
        return message;
    }

    public static Message collateMessages(Message msg, MessageBank messageBank) throws Exception {
        Message earliestMessage = null;
        String tripType = msg.tripType;
        int hopCount = msg.hopCount;
        String messageId = msg.route.get(msg.hopCount).messageId;
        String destinationName = msg.destinationName;
        String earliestTime = "";

        if (tripType.equals("FastestTrip")) {
            for (Message message : messageBank.bank) {
                try {
                    if (message.routeEndFound == false
                            && message.route.get(message.hopCount).messageId.equals(messageId)) {
                        earliestTime = message.route.get(message.route.size() - 1).earliestTrips.get(0).get(3);
                        earliestMessage = message;
                        break;
                    }
                } catch (Exception e) {
                    // do nothing - the message is some other message that doesn't have the same
                    throw e;
                }
            }
            for (Message message : messageBank.bank) {
                try {
                    if (message.routeEndFound == false
                            && message.route.get(message.route.size() - 1).earliestTrips.size() > 0
                            && message.route.get(message.hopCount).messageId.equals(messageId)) {
                        String compareEarliestTime = message.route.get(message.route.size() - 1).earliestTrips.get(0)
                                .get(3);
                        Date dteCompareEarliestTime = new SimpleDateFormat("HH:mm").parse(compareEarliestTime);
                        Date dteEarliestTime = new SimpleDateFormat("HH:mm").parse(earliestTime);
                        if (dteCompareEarliestTime.compareTo(dteEarliestTime) < 0) {
                            earliestTime = compareEarliestTime;
                            earliestMessage = message;
                        }
                    }
                } catch (Exception e) {
                    // do nothing. the message is some other mssage that doens't have to same
                    // hopCount
                    throw e;
                }
            }
        }

        // remove message from message bank
        messageBank.removeMessage(hopCount, messageId);

        if (earliestMessage != null) {
            return earliestMessage;
        } else {
            msg.routeEndFound = true;
            msg.messageType = "incoming";
            return msg;
        }
    }

    /**
     * Checks if the message has visited all stations in the route. If 0, that means
     * that there is no earliest trip from the station and hence no route is found.
     * 
     * @param msg
     * @return number of stations not yet visited
     */
    public static int removeVisitedFromEarliestTrips(Message msg) {
        int visited = 0;
        for (List<String> trip : msg.route.get(msg.hopCount).earliestTrips) {
            for (StationObject route : msg.route) {
                if (trip.get(4).equals(route.stationName)) {
                    visited++;
                }
            }
        }
        return msg.route.get(msg.hopCount).earliestTrips.size() - visited;
    }

    /**
     * Determines if there is a dead-end
     * 
     * @param station
     * @param msg
     * @return true if there is a dead-end. returns false otherwise.
     */
    public static Boolean routeEnd(Station station, Message msg) {
        List<Boolean> visited = new ArrayList<Boolean>();
        List<StationObject> routes = msg.route;

        if (removeVisitedFromEarliestTrips(msg) == 0) {
            return true;
        }

        for (Station neighbour : station.neighbours) {
            Boolean visit = false;
            for (StationObject route : routes) {
                if (route.stationUDPAddress.equals(neighbour.getStationUdpAddress())) {
                    visit = true;
                    break;
                }
            }
            visited.add(visit);
        }

        for (Boolean visit : visited) {
            if (visit == false) {
                return false;
            }
        }

        return true;
    }

    /**
     * Checks if the station exists in the earliest trip list in message
     * 
     * @param msg
     * @param station
     * @return true if it exists, false otherwise.
     */
    public static Boolean checkStationInEarliestTrips(Message msg, Station station) {
        for (List<String> trip : msg.route.get(msg.hopCount).earliestTrips) {
            if (trip.get(4).equals(station.stationName)) {
                return true;
            }
        }
        return false;
    }

    /**
     * Find the position in the route list with the specified station name
     * 
     * @param route
     * @param stationName
     * @return position index
     */
    public static int findRoutePosition(List<StationObject> route, String stationName) {
        for (int index = 0; index < route.size(); index++) {
            if (route.get(index).stationName.equals(stationName)) {
                return index;
            }
        }
        return -1; // not found
    }

    /**
     * Updates the timetable if the file last modified time has changed
     * 
     * @param station
     * @param path
     * @param fileTime
     * @return
     * @throws Exception
     */
    public static Long checkAndUpdateTimetable(Station station, String path, Long fileTime) throws Exception {
        Long modifiedTime = new File(path).lastModified();
        if (fileTime.longValue() != modifiedTime.longValue()) {
            List<List<String>> timetable = getTimetable(path);
            // set timetable
            station.setTimetable(timetable);
            System.out.println("file modified. udpated time: " + modifiedTime);
            return modifiedTime;
        }
        return fileTime;
    }

    /**
     * Obtain args and set values for Station
     * 
     * @param args input arguments
     */
    public static List<Object> getArguments(String[] args) {
        String stationName = new String();
        String tcpPort = new String();
        String udpPort = new String();
        List<String> neighbourPorts = new ArrayList<String>();

        for (int i = 0; i < args.length; i++) {
            if (i == 0) {
                // station name argument
                stationName = args[i];
            } else if (i == 1) {
                // tcpPort argument
                tcpPort = args[i];
            } else if (i == 2) {
                // udpPort argument
                udpPort = args[i];
            } else {
                // neighbour ports
                neighbourPorts.add(args[i]);
            }
        }
        System.out.println("StationName: " + stationName);
        System.out.println("TcpPort: " + tcpPort);
        System.out.println("UdpPort: " + udpPort);
        Station station = new Station(stationName, tcpPort, udpPort);

        return Arrays.asList(station, neighbourPorts);
    }

    public static List<List<String>> getTimetable(String path) throws Exception {
        List<List<String>> records = new ArrayList<>();
        try (BufferedReader br = new BufferedReader(new FileReader(path))) {
            String headerLine = br.readLine(); // read the header line but do nothing with it
            String line;
            while ((line = br.readLine()) != null) {
                String[] values = line.split(",");
                records.add(Arrays.asList(values));
            }
            br.close();
        } catch (Exception e) {
            throw new Exception("Failed to get timetable. Full error:\n" + e);
        }
        return records;
    }

    public static void addNeighbour(List<String> neighbourPorts, Station station) {
        for (String neighbourPort : neighbourPorts) {
            Station neighbour = new Station("", "", neighbourPort);
            station.addNeighbour(neighbour);
        }
    }

    public static void checkArguments(String[] args) throws Exception {
        if (args.length < 3) {
            throw new Exception(
                    "Please at least provide (1) Station Name, (2) Station's TCP Port, (3) Station's UDP Port. (Optional) Provide neighbour ports.");
        }
    }

    public static String modifyHtmlContent(String htmlContent, String summarisedTrip, String station, String timetable,
            String stationTcpAddress, String tripTypes, String stationResponse, String responses,
            String routeEndFound) {
        htmlContent = htmlContent.replace("{summarisedTrip}", summarisedTrip);
        htmlContent = htmlContent.replace("{station}", station);
        htmlContent = htmlContent.replace("{timetable}", timetable);
        htmlContent = htmlContent.replace("{stationTcpAddress}", stationTcpAddress);
        htmlContent = htmlContent.replace("{tripTypes}", tripTypes);
        htmlContent = htmlContent.replace("{stationResponse}", stationResponse);
        htmlContent = htmlContent.replace("{responses}", responses);
        htmlContent = htmlContent.replace("{routeEndFound}", routeEndFound);
        return htmlContent;
    }

    public void sendUdpToParent(Station station, Message msg, int hopCountDeduct, DatagramChannel datagramChannel)
            throws Exception {
        msg.messageType = "incoming";
        msg.hopCount = msg.hopCount - hopCountDeduct;
        Gson gson = new Gson();
        String msgString = gson.toJson(msg);
        StationObject parent = msg.route.get(msg.hopCount);
        String parentUdpAddress = parent.stationUDPAddress.replace("http://", "");
        String parentHost = parentUdpAddress.split(":")[0];
        String parentPort = parentUdpAddress.split(":")[1];
        ByteBuffer datagramSendBuffer = ByteBuffer.wrap(msgString.getBytes());

        try {
            System.out.println("Sending message to parent: " + parentHost + ":" + parentPort);
            datagramChannel.send(datagramSendBuffer, new InetSocketAddress(parentHost, Integer.parseInt(parentPort)));
            System.out.println("Msg sent to parent: " + parentHost + ":" + parentPort);
            datagramSendBuffer.clear();
        } catch (Exception e) {
            // do nothing
            throw e;
        }
    }

    public Boolean sendUdp(Station station, Message msg, MessageSentLogs messageSentLogs,
            DatagramChannel datagramChannel) {
        Gson gson = new Gson();
        String msgString = gson.toJson(msg);
        ByteBuffer datagramSendBuffer = ByteBuffer.wrap(msgString.getBytes());
        int sentToNeighbours = 0;
        for (Station neighbour : station.neighbours) {
            // set send to true initially
            Boolean send = true;
            // don't send to stations that are already in message
            for (StationObject route : msg.route) {
                if (route.stationUDPAddress.equals(neighbour.getStationUdpAddress())) {
                    send = false;
                }
            }
            // don't send message to stations that a messageId exists in messageSentLogs
            for (MessageSentLog log : messageSentLogs.logs) {
                if (msg.messageId.equals(log.messageId)
                        && neighbour.getStationUdpAddress().equals(log.destinationStationAddress)) {
                    send = false;
                }
            }

            if (send) {
                if (msg.hopCount == 0) {
                    MessageSentLog newLog = new MessageSentLog(msg.route.get(msg.hopCount).messageId, "",
                            station.getStationUdpAddress(), neighbour.getStationUdpAddress());
                    messageSentLogs.addLog(newLog);
                } else {
                    MessageSentLog newLog = new MessageSentLog(msg.route.get(msg.hopCount).messageId,
                            msg.route.get(msg.hopCount - 1).stationUDPAddress, station.getStationUdpAddress(),
                            neighbour.getStationUdpAddress());
                    messageSentLogs.addLog(newLog);
                }
                try {
                    datagramChannel.send(datagramSendBuffer, new InetSocketAddress(station.server, neighbour.udpPort));
                    datagramSendBuffer.clear();
                    System.out.println("Msg Sent to neighbour: " + neighbour.getStationUdpAddress());
                    sentToNeighbours++;
                } catch (Exception e) {
                    // nothing
                }
            }
        }
        if (sentToNeighbours == 0) {
            return false;
        }
        return true;
    }

    public static List<List<String>> collateEarliestTrips(Message msg) {
        List<List<String>> earliestTrips = new ArrayList<List<String>>();
        for (StationObject route : msg.route) {
            earliestTrips.add(route.earliestTrips.get(0));
        }
        return earliestTrips;
    }

    public void startStation(String[] args) throws Exception {
        // check arguments
        checkArguments(args);
        // get arguments
        List<Object> argResult = getArguments(args);
        Station station = (Station) argResult.get(0);
        List<String> neighbourPorts = (List<String>) argResult.get(1);
        // add neighbours
        addNeighbour(neighbourPorts, station);
        for (Station neighbour : station.neighbours) {
            System.out.println("Neighbour port: " + neighbour.udpPort);
        }
        // get file path
        String path = System.getProperty("user.dir") + "/tt-" + station.stationName;
        System.out.println("Path: " + path);
        // get timetable
        List<List<String>> timetable = getTimetable(path);
        // set timetable
        station.setTimetable(timetable);
        for (List<String> record : timetable) {
            System.out.println("Record: " + record);
        }
        Long fileTime = new File(path).lastModified();
        String htmlPathString = System.getProperty("user.dir") + "/station.html";
        Path htmlPath = Paths.get(htmlPathString);
        String htmlTemplate = Files.readString(htmlPath, StandardCharsets.US_ASCII);

        // create and open the selector
        Selector selector = Selector.open();
        // tcp: create server socket channel
        ServerSocketChannel serverSocketChannel = ServerSocketChannel.open();
        InetSocketAddress tcpServerAddress = new InetSocketAddress(station.server, station.tcpPort);
        // bind the channel's socket to a local address and configures the socket to
        // listen for connections
        serverSocketChannel.bind(tcpServerAddress);
        // set to non-blocking
        serverSocketChannel.configureBlocking(false);
        // obtain valid operations
        int ops = serverSocketChannel.validOps();
        // register the selector
        SelectionKey selectKy = serverSocketChannel.register(selector, ops, station.tcpPort);

        // udp: create datagram channel
        DatagramChannel datagramChannel = DatagramChannel.open();
        InetSocketAddress udpServerAddress = new InetSocketAddress(station.server, station.udpPort);
        datagramChannel.configureBlocking(false);
        datagramChannel.socket().bind(udpServerAddress);
        datagramChannel.register(selector, SelectionKey.OP_READ, station.udpPort);

        // create logs
        MessageSentLogs messageSentLogs = new MessageSentLogs();
        MessageBank messageBank = new MessageBank();
        ClientRequestLog clientRequestLog = new ClientRequestLog();

        // start listening
        while (true) {
            // System.out.println("Sever has started: " + tcpServerAddress);
            selector.select();
            System.out.println("Selector: " + selector);
            Set<SelectionKey> selectedKeys = selector.selectedKeys();
            Iterator<SelectionKey> keyIterator = selectedKeys.iterator();
            while (keyIterator.hasNext()) {
                // check and update timetable
                fileTime = checkAndUpdateTimetable(station, path, fileTime);
                SelectionKey key = keyIterator.next(); // (SelectionKey)
                System.out.println("Key attachment: " + key.attachment());
                // accept

                if (key.isAcceptable()) {
                    if ((int) key.attachment() == station.tcpPort) {
                        SocketChannel socketChannel = serverSocketChannel.accept();
                        System.out.println("Port: " + socketChannel.getLocalAddress().toString().split(":")[1]);
                        socketChannel.configureBlocking(false);
                        // register the socketChannel for read operations
                        socketChannel.register(selector, SelectionKey.OP_READ, station.tcpPort);
                        System.out.println("Connection accepted: " + socketChannel.getLocalAddress() + "\n");
                    }
                }
                // readable
                if (key.isReadable()) {
                    String htmlContent = new String();
                    htmlContent = htmlTemplate;
                    if ((int) key.attachment() == station.tcpPort) {
                        // obtain the socket channel from the selector key
                        SocketChannel socketChannel = (SocketChannel) key.channel();
                        ByteBuffer buffer = ByteBuffer.allocate(1024);
                        // read from socket to a buffer
                        socketChannel.read(buffer);
                        // store contents from buffer into a string
                        String requestBody = new String(buffer.array()).trim();
                        System.out.println("Message received: " + requestBody);
                        requestBody = getRequestBody(requestBody);
                        if (requestBody.indexOf("to") != -1) {
                            // contains message
                            List<HashMap<String, String>> requestMap = getRequestObject(requestBody);
                            System.out.println("Request Map : " + requestMap);
                            String messageId = UUID.randomUUID().toString();
                            System.out.println("Message received. Generate message ID: " + messageId);
                            Message msg = station.getMessageToSend(requestMap, station, messageId);
                            Gson testGson = new Gson();
                            System.out.println("msg: " + testGson.toJson(msg) + "\n");
                            List<Object> findDestResult = findDestination(station, msg);
                            Boolean destFound = (Boolean) findDestResult.get(0);
                            List<String> earliestTrip = (List<String>) findDestResult.get(1);
                            System.out.println("Destination found: " + destFound);
                            System.out.println("earliestTrip found: " + earliestTrip);
                            if (destFound) {
                                msg = matchRoute(msg);
                                msg = addRouteStationToTripDetails(msg);
                                List<List<String>> earliestTripsList = collateEarliestTrips(msg);
                                System.out.println("Match route: " + testGson.toJson(msg));
                                String summarisedTrip = getSummarisedTrip(msg);
                                System.out.println("summarisedTrip: " + summarisedTrip);
                                Gson gson = new Gson();
                                htmlContent = modifyHtmlContent(htmlContent, summarisedTrip, station.stationName,
                                        gson.toJson(station.timetable), station.getStationTcpAddress(),
                                        gson.toJson(station.TRIP_TYPE), "true", gson.toJson(earliestTripsList),
                                        "false");
                                System.out.println("---- Converted html content ----- ");
                                String message = "HTTP/1.1 200 OK\r\n\r\n" + htmlContent;
                                System.out.println("Message length: " + message.length());
                                ByteBuffer responseBuffer = ByteBuffer.allocate(message.length());
                                responseBuffer.clear();
                                responseBuffer.put(message.getBytes());
                                responseBuffer.flip();
                                while (responseBuffer.hasRemaining()) {
                                    socketChannel.write(responseBuffer);
                                }
                                socketChannel.close();
                            } else {
                                // send UDP to neighbours
                                Boolean sentToNeighbours = sendUdp(station, msg, messageSentLogs, datagramChannel);
                                // Store client request and socket channel in log (single log)
                                clientRequestLog.setSocketChannel(socketChannel);
                            }
                        } else {
                            System.out.println("RETURN EMPTY PAGE TO CLIENT");
                            Gson gson = new Gson();
                            // send empty page to client
                            htmlContent = modifyHtmlContent(htmlContent, "", station.stationName,
                                    gson.toJson(station.timetable), station.getStationTcpAddress(),
                                    gson.toJson(station.TRIP_TYPE), "false", gson.toJson(""), "false");
                            String message = "HTTP/1.1 200 OK\r\n\r\n" + htmlContent;
                            System.out.println("Message length: " + message.length());
                            ByteBuffer responseBuffer = ByteBuffer.allocate(message.length());
                            responseBuffer.clear();
                            responseBuffer.put(message.getBytes());
                            responseBuffer.flip();
                            while (responseBuffer.hasRemaining()) {
                                socketChannel.write(responseBuffer);
                            }
                            socketChannel.close();
                        }
                    } else if ((int) key.attachment() == station.udpPort) {
                        // Receive message
                        DatagramChannel dgChannel = (DatagramChannel) key.channel();
                        ByteBuffer datagramBuffer = ByteBuffer.allocate(station.messageSize);
                        InetSocketAddress remoteAddress = (InetSocketAddress) dgChannel.receive(datagramBuffer); // SocketAddress
                        // remoteAddress =
                        // SocketAddress remoteAddress = dgChannel.getRemoteAddress();
                        datagramBuffer.flip();
                        int limits = datagramBuffer.limit();
                        byte bytes[] = new byte[limits];
                        datagramBuffer.get(bytes, 0, limits);
                        String msgString = new String(bytes);
                        Gson gson = new Gson();
                        Message msg = gson.fromJson(msgString, Message.class);
                        System.out.println("Client at: " + remoteAddress + " ||  sent message: " + gson.toJson(msg));
                        // dgChannel.close();

                        // INCOMING MESSAGE
                        if (msg.messageType.equals("incoming")) {
                            // Receive message
                            if (msg.sourceName.equals(station.stationName)) {
                                // ARRIVED BACK AT SOURCE
                                messageBank.addMessage(msg);
                                String destinationStationAddress = "http:/" + remoteAddress;
                                String removeMessageId = msg.route.get(msg.hopCount).messageId;
                                String parentAddress = ""; // no parent address as this is the source
                                MessageSentLog removedLog = messageSentLogs.removeLog(parentAddress,
                                        destinationStationAddress, removeMessageId);
                                if (removedLog == null) {
                                    // Failed to remove log
                                    throw new Exception("Failed to remove log");
                                }
                                if (messageSentLogs.getLogs(removedLog.messageId) == null) {
                                    // No more logs left for this messageId
                                    // collate results and send back to client
                                    Message collatedMessage = collateMessages(msg, messageBank);
                                    collatedMessage = matchRoute(collatedMessage);
                                    Boolean routeEndFound = collatedMessage.routeEndFound;
                                    if (!routeEndFound) {
                                        // No dead end found
                                        msg = addRouteStationToTripDetails(collatedMessage);
                                        String summarisedTrip = getSummarisedTrip(collatedMessage);
                                        List<List<String>> earliestTripsList = collateEarliestTrips(msg);
                                        // modify html content
                                        htmlContent = modifyHtmlContent(htmlContent, summarisedTrip,
                                                station.stationName, gson.toJson(station.timetable),
                                                station.getStationTcpAddress(), gson.toJson(station.TRIP_TYPE), "true",
                                                gson.toJson(earliestTripsList), gson.toJson(routeEndFound));
                                    } else {
                                        htmlContent = modifyHtmlContent(htmlContent, "Oh uh! No route found!",
                                                station.stationName, gson.toJson(station.timetable),
                                                station.getStationTcpAddress(), gson.toJson(station.TRIP_TYPE), "true",
                                                gson.toJson(""), "true");
                                    }
                                    // get open tCP socket channel
                                    SocketChannel socketChannel = clientRequestLog.getSocketChannel();
                                    String message = "HTTP/1.1 200 OK\r\n\r\n" + htmlContent;
                                    System.out.println("Message length: " + message.length());
                                    ByteBuffer responseBuffer = ByteBuffer.allocate(message.length());
                                    responseBuffer.clear();
                                    responseBuffer.put(message.getBytes());
                                    responseBuffer.flip();
                                    while (responseBuffer.hasRemaining()) {
                                        socketChannel.write(responseBuffer);
                                    }
                                    socketChannel.close();
                                }
                            } else {
                                // NOT YET AT SOURCE - CHECK IF CAN COLLATE AND SEND BACK TO PARENT
                                messageBank.addMessage(msg);
                                String destinationStationAddress = "http:/" + remoteAddress;
                                String removeMessageId = msg.route.get(msg.hopCount).messageId;
                                String parentAddress = msg.route.get(msg.hopCount - 1).stationUDPAddress;
                                MessageSentLog removedLog = messageSentLogs.removeLog(parentAddress,
                                        destinationStationAddress, removeMessageId);
                                if (messageSentLogs.getLogs(removedLog.messageId) == null) {
                                    // No more logs left for this messageId
                                    // collate results and send back to parent
                                    System.out.println("Begin collating message to send back to parent.");
                                    Message collatedMessage = collateMessages(msg, messageBank);
                                    System.out.println("message collated.");
                                    System.out.println("Begin matching route.");
                                    collatedMessage = matchRoute(collatedMessage);
                                    System.out.println("Matching route completed.");
                                    // -1 hopCount because we want to
                                    // decrement the hopCount as we
                                    // return back to source
                                    System.out.println("Begin sending to parent.");
                                    sendUdpToParent(station, msg, 1, datagramChannel);
                                    System.out.println("Send to parent complete.");
                                } else {
                                    System.out.println("Logs remaining."
                                            + gson.toJson(messageSentLogs.getLogs(removedLog.messageId)));
                                }
                            }

                        } else {
                            // OUTGOING MESSAGE
                            if (msg.destinationName.equals(station.stationName)) {
                                // I AM SOURCE STATION. DEAD END FOUND.
                                msg.routeEndFound = true;
                                sendUdpToParent(station, msg, 0, datagramChannel);
                            } else {
                                // IS THE MESSAGE INTENDED FOR ME?
                                Boolean messageIntended = checkStationInEarliestTrips(msg, station);
                                if (messageIntended) {
                                    // INTENDED
                                    String messageId = UUID.randomUUID().toString();
                                    System.out.println("Message received. Generate message ID: " + messageId);
                                    msg = addStationToRoute(msg, station, messageId);
                                    List<Object> findDestResult = findDestination(station, msg);
                                    Boolean destFound = (Boolean) findDestResult.get(0);
                                    List<String> earliestTrip = (List<String>) findDestResult.get(1);
                                    System.out.println("Destination found: " + destFound);
                                    System.out.println("earliestTrip found: " + earliestTrip);
                                    Boolean routeEndFound = routeEnd(station, msg);
                                    if (destFound == true && routeEndFound == true) {
                                        // DEAD END FOUND
                                        msg.routeEndFound = true;
                                        // let parent know that a deadend is found
                                        sendUdpToParent(station, msg, 1, datagramChannel);
                                    }
                                    if (destFound == true && routeEndFound == false) {
                                        // DESTINATION FOUND AND NOT A DEAD END
                                        // SEND MESSAGE BACK TO PARENT
                                        System.out.println("Removing non destination");
                                        msg = removeNonDestination(msg, station);
                                        System.out.println("Sending to parent non destination");
                                        sendUdpToParent(station, msg, 1, datagramChannel);
                                    }
                                    if (destFound == false && routeEndFound == false) {
                                        // SEND MESSAGE TO NEIGHBOURS
                                        Boolean sentToNeighbours = sendUdp(station, msg, messageSentLogs,
                                                datagramChannel);
                                        if (!sentToNeighbours) {
                                            // failed to send to neighbours as dead end is found
                                            // set route end to true
                                            msg.routeEndFound = true;
                                            // send to parent instead
                                            sendUdpToParent(station, msg, 1, datagramChannel);
                                        }
                                    }
                                    if (destFound == false && routeEndFound == true) {
                                        // DEAD END IS FOUND AND DEST NOT FOUND
                                        msg.routeEndFound = true;
                                        // SEND BACK TO PARENT
                                        sendUdpToParent(station, msg, 1, datagramChannel);
                                    }
                                } else {
                                    // NOT INTENDED FOR ME
                                    // Marks msg as Route end found
                                    msg.routeEndFound = true;
                                    // SEND BACK TO PARENT
                                    sendUdpToParent(station, msg, 0, datagramChannel);
                                }
                            }
                        }
                    }
                }
                // remove the key iterator when done using it
                keyIterator.remove();
            }
        }

    }

    public static void main(String[] args) throws Exception {
        Station station = new Station();
        station.startStation(args);
    }
}