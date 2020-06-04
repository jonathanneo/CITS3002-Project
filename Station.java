import java.nio.channels.ServerSocketChannel;
import java.nio.channels.SocketChannel;
import java.nio.channels.Selector;
import java.nio.channels.SelectionKey;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.io.*;
import java.net.InetSocketAddress;
import java.net.ServerSocket;
import java.net.Socket;
import java.util.Iterator;
import java.util.Set;

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

    /**
     * Obtain args and set values for Station
     * 
     * @param args input arguments
     */
    static private List<Object> getArguments(String[] args) {

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

    public static void listenTcpServer() {

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
        SelectionKey selectKy = serverSocketChannel.register(selector, ops, null); // , null
        System.out.println("Sever has started: " + tcpServerAddress);
        // start listening
        while (true) {

            selector.select();
            System.out.println("Selector: " + selector);
            Set<SelectionKey> selectedKeys = selector.selectedKeys();
            Iterator<SelectionKey> keyIterator = selectedKeys.iterator();
            while (keyIterator.hasNext()) {
                SelectionKey key = keyIterator.next(); // (SelectionKey)
                // accept
                if (key.isAcceptable()) {
                    SocketChannel socketChannel = serverSocketChannel.accept();
                    System.out.println("Port: " + socketChannel.getLocalAddress().toString().split(":")[1]);
                    socketChannel.configureBlocking(false);
                    // register the socketChannel for read operations
                    socketChannel.register(selector, SelectionKey.OP_READ);
                    System.out.println("Connection accepted: " + socketChannel.getLocalAddress() + "\n");
                } else if (key.isReadable()) {
                    // obtain the socket channel from the selector key
                    SocketChannel socketChannel = (SocketChannel) key.channel();
                    ByteBuffer buffer = ByteBuffer.allocate(1024);
                    // read from socket to a buffer
                    socketChannel.read(buffer);
                    // store contents from buffer into a string
                    String result = new String(buffer.array()).trim();
                    System.out.println("Message received: " + result);

                    // DO STUFF HERE AND SEND RESPONSE BACK TO CLIENT

                    String message = "HTTP/1.1 200 OK\r\n\r\n Hello there!";
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
                // remove the key iterator when done using it
                keyIterator.remove();
            }
        }
    }
}