import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.io.*;

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
    String tcpPort;
    String udpPort;
    String tcpAddress;
    String udpAddress;
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
        this.tcpPort = tcpPort;
        this.udpPort = udpPort;
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

    public List<List<String>> getTimetable(String path) throws Exception {
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

    public static void main(String[] args) throws Exception {
        if (args.length < 3) {
            throw new Exception(
                    "Please at least provide (1) Station Name, (2) Station's TCP Port, (3) Station's UDP Port. (Optional) Provide neighbour ports.");
        }

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

    }
}