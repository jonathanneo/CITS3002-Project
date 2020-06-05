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
    String TRIP_TYPE = "FastestTrip";
    int MESSAGE_SIZE = 10000;

    // variables
    String stationName;
    int messageSize;
    int tcpPort;
    int udpPort;
    String format;
    String server;
    List<Station> neighbours;
    List<List<String>> timetable;

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
                        earliestTrips.add(timetableRecord);
                    }
                } else {
                    Boolean recordFound = false;
                    for (List<String> trips : earliestTrips) {
                        if (timetableRecordTime.compareTo(timeValue) >= 0
                                && trips.get(4) == timetableRecordDestination) {
                            recordFound = true;
                        }
                    }
                    if (recordFound == false) {
                        earliestTrips.add(timetableRecord);
                    }
                }
            }
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
     * Subclass for ClientRequestLog which is used to store requests from the client
     */
    public class ClientRequestLog {
        // TODO: update if needed
    }

    /**
     * Subclass for ClientRequestLogs which is used to store a list of requests from
     * the client
     */
    public class ClientRequestLogs {
        // TODO: update if needed
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
        public MessageSentLog removeLog(String parentAddress, String destinationStationAddress, String messageId) {
            for (MessageSentLog log : this.logs) {
                if (log.parentAddress == parentAddress && log.destinationStationAddress == destinationStationAddress
                        && log.messageId == messageId) {
                    this.logs.remove(log);
                    return log;
                }
            }
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
                if (log.messageId == messageId) {
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
                    if (bankMessageId == messageId) {
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
    public static String getRequestBody(List<String> requestArray) {
        String requestString = (String) requestArray.get(0);
        String[] requestStringList = requestString.split(" ");
        requestString = requestStringList[1];
        requestString = requestString.replace("/?", "");
        return requestString;
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
                    if (trip.get(4) != nextRoute.stationName) {
                        removeTrip.add(trip);
                    }
                }
            } else {
                for (List<String> trip : earliestTrips) {
                    if (trip.get(4) != msg.destinationName) {
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
        if (time == "") {
            Date date = new Date();
            SimpleDateFormat formatter = new SimpleDateFormat("HH:mm");
            time = formatter.format(date);
        }
        if (tripType == "") {
            tripType = "FastestTrip";
        }
        Message message = new Message(station.stationName, destination, tripType, time, messageId, messageType);
        message.addRoute(station);
        return message;
    }

    public static List<Object> findDestination(Station station, Message msg) {
        List<Object> returnList = new ArrayList<Object>();
        String destinationName = msg.destinationName;
        List<StationObject> routes = msg.route;
        StationObject route = routes.get(msg.hopCount);
        for (List<String> trip : route.earliestTrips) {
            if (trip.get(4) == destinationName) {
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
        List<String> sourceTrip = msg.route.get(0).earliestTrips.get(0);
        List<String> destinationTrip = msg.route.get(msg.route.size() - 1).earliestTrips.get(0);
        String summarisedTrip = "Depart from " + sourceName + " (" + sourceTrip.get(3) + ") taking " + sourceTrip.get(2)
                + " and eventually arrive at " + destinationName + " at " + destinationTrip.get(4)
                + ". View trip details below.";
        return summarisedTrip;
    }

    public static Message removeNonDestination(Message message, Station station) {
        List<List<String>> newEarliestTrips = new ArrayList<List<String>>();
        String destination = message.destinationName;
        List<List<String>> earliestTrips = message.route.get(message.hopCount).earliestTrips;
        for (List<String> trip : earliestTrips) {
            if (trip.get(4) == destination) {
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
            if (trip.get(4) == station.stationName) {
                lastRouteTime = trip.get(3);
            }
        }
        StationObject stationObject = station.getStationObject(messageId, lastRouteTime);
        message.route.add(stationObject);
        message.hopCount++;
        return message;
    }

    public static Message collateMessages(Message msg, MessageBank messageBank) {
        Message earliestMessage = null;
        String tripType = msg.tripType;
        int hopCount = msg.hopCount;
        String messageId = msg.route.get(msg.hopCount).messageId;
        String destinationName = msg.destinationName;
        String earliestTime = "";

        if (tripType == "FastestTrip") {
            for (Message message : messageBank.bank) {
                try {
                    if (message.routeEndFound == false && message.route.get(message.hopCount).messageId == messageId) {
                        earliestTime = message.route.get(message.route.size() - 1).earliestTrips.get(0).get(4);
                        earliestMessage = message;
                        break;
                    }
                } catch (Exception e) {
                    // do nothing - the message is some other message that doesn't have the same
                    // hopCount
                }
            }
            for (Message message : messageBank.bank) {
                try {
                    if (message.routeEndFound == false
                            && message.route.get(message.route.size() - 1).earliestTrips.size() > 0
                            && message.route.get(message.hopCount).messageId == messageId) {
                        String compareEarliestTime = message.route.get(message.route.size() - 1).earliestTrips.get(0)
                                .get(4);
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
                }
            }
        }
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
                if (trip.get(4) == route.stationName) {
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
                if (route.stationUDPAddress == neighbour.getStationUdpAddress()) {
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
            if (trip.get(4) == station.stationName) {
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
            if (route.get(index).stationName == stationName) {
                return index;
            }
        }
        return -1; // not found
    }

    public static Long checkAndUpdateTimetable(Station station, String path, Long fileTime) throws Exception {
        Long modifiedTime = new File(path).lastModified();
        if (fileTime != modifiedTime) {
            List<List<String>> timetable = getTimetable(path);
            // set timetable
            station.setTimetable(timetable);
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

    public static void main(String[] args) throws Exception {
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
        String htmlPathString = System.getProperty("user.dir") + "/station.html";
        Path htmlPath = Paths.get(htmlPathString);
        // String htmlContent = getHtmlContent(htmlPath, station.format);
        String htmlContent = Files.readString(htmlPath, StandardCharsets.US_ASCII);
        htmlContent = htmlContent.replace("{summarisedTrip}", "Hello There!");
        htmlContent = htmlContent.replace("{station}", station.stationName);
        System.out.println("HTML Content" + htmlContent);

        // create and open the selector
        Selector selector = Selector.open();
        // tcp: create server socket channel
        ServerSocketChannel serverSocketChannel = ServerSocketChannel.open();
        InetSocketAddress tcpServerAddress = new InetSocketAddress(station.server, station.tcpPort);
        // HashMap<String, InetSocketAddress> tcpServerAddressHashMap = new
        // HashMap<String, InetSocketAddress>();
        // tcpServerAddressHashMap.put("address", tcpServerAddress);
        // bind the channel's socket to a local address and configures the socket to
        // listen for connections
        serverSocketChannel.bind(tcpServerAddress);
        // set to non-blocking
        serverSocketChannel.configureBlocking(false);
        // obtain valid operations
        int ops = serverSocketChannel.validOps();
        // register the selector
        SelectionKey selectKy = serverSocketChannel.register(selector, ops, station.tcpPort); // , null

        // udp: create datagram channel
        DatagramChannel datagramChannel = DatagramChannel.open();
        InetSocketAddress udpServerAddress = new InetSocketAddress(station.server, station.udpPort);
        // HashMap<String, InetSocketAddress> udpServerAddressHashMap = new
        // HashMap<String, InetSocketAddress>();
        // udpServerAddressHashMap.put("address", udpServerAddress);
        datagramChannel.configureBlocking(false);
        datagramChannel.socket().bind(udpServerAddress);
        datagramChannel.register(selector, SelectionKey.OP_READ, station.udpPort);

        // start listening
        while (true) {
            System.out.println("Sever has started: " + tcpServerAddress);
            selector.select();
            System.out.println("Selector: " + selector);
            Set<SelectionKey> selectedKeys = selector.selectedKeys();
            Iterator<SelectionKey> keyIterator = selectedKeys.iterator();
            while (keyIterator.hasNext()) {
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

                    if ((int) key.attachment() == station.tcpPort) {
                        // obtain the socket channel from the selector key
                        SocketChannel socketChannel = (SocketChannel) key.channel();
                        ByteBuffer buffer = ByteBuffer.allocate(1024);
                        // read from socket to a buffer
                        socketChannel.read(buffer);
                        // store contents from buffer into a string
                        String result = new String(buffer.array()).trim();
                        System.out.println("Message received: " + result);

                        // DO STUFF HERE AND SEND RESPONSE BACK TO CLIENT

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
                    } else if ((int) key.attachment() == station.udpPort) {
                        // System.out.println("Message received from UDP!!");
                        DatagramChannel dgChannel = (DatagramChannel) key.channel();
                        ByteBuffer datagramBuffer = ByteBuffer.allocate(station.messageSize);
                        SocketAddress remoteAddress = dgChannel.receive(datagramBuffer);
                        datagramBuffer.flip();
                        int limits = datagramBuffer.limit();
                        byte bytes[] = new byte[limits];
                        datagramBuffer.get(bytes, 0, limits);
                        String msg = new String(bytes);
                        System.out.println("Client at: " + remoteAddress + " ||  sent message: " + msg);
                        dgChannel.close();

                        // DO STUFF WITH DATAGRAM MESSAGE

                        DatagramChannel dgSendChannel = DatagramChannel.open();
                        String datagramSendMsg = "Right back at ya!";
                        ByteBuffer datagramSendBuffer = ByteBuffer.wrap(datagramSendMsg.getBytes());
                        dgSendChannel.send(datagramSendBuffer, new InetSocketAddress(station.server,
                                Integer.parseInt(remoteAddress.toString().split(":")[1])));
                        datagramSendBuffer.clear();
                        dgSendChannel.close();
                        // for (Station neighbour : station.neighbours) {
                        // dgSendChannel.send(datagramSendBuffer,
                        // new InetSocketAddress(station.server, neighbour.udpPort));
                        // datagramSendBuffer.clear();
                        // dgSendChannel.close();
                        // }

                    }
                }
                // remove the key iterator when done using it
                keyIterator.remove();
            }
        }
    }
}