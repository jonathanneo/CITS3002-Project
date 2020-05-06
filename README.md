# CITS3001 Project

The goal of this project is to develop a server application to manage the data and permit queries about Transperth bus and train routes. By successfully completing the project, you will have a greater understanding of the standard TCP and UDP protocols running over IP, communication between web-browsers and application programs using HTTP and HTML, and will have developed a simple text-based protocol to make and reply to queries for distributed information.

# Operating system

Operating system: Microsoft Windows 10 Pro, Windows Subsystem for Linux (WSL)

# Transperth data

Perth's Public Transport Authority (PTA, or Transperth) provides public access to its scheduled times, stop locations, and route information from its webpage www.transperth.wa.gov.au/About/Spatial-Data-Access.

# Testing

We will approach the project using connected networks of increasing size: 1 station, 2 stations, 5 stations, 10 stations, 20 stations,....
Note that running more than 10 Java virtual machines on a single computer will probably not be possible.

# Resources

- Project Information: https://teaching.csse.uwa.edu.au/units/CITS3002/project2020/index.php
- Getting Started (really helpful!): https://teaching.csse.uwa.edu.au/units/CITS3002/project2020/getting-started.php
- Clarifications: https://teaching.csse.uwa.edu.au/units/CITS3002/project2020/clarifications.php

# Networking Details

Typical invocation e.g.:

    ./station Warwick-Stn 2401 2408 2560 2566

- Station name: Warwick-Stn
- TCP/IP port (listening for queries from webpage): 2401
- UDP/IP port (listening for other stations): 2408
- Physically adjacent to (stations with UDP ports): 2560, 2566

1. Each station server is its own process.
2. All station servers execute on the same computer. Thus all network traffic/URLs will refer to localhost or 127.0.0.
3. Query and reply will be transmitted using the (minimum amount necessary) HTTP, HTML, over bidirectional TCP/IP connection. After each query and response, the station must close the connection. If either station or webpage crash the connection will be closed.
4. Stations communicate to each other through UDP/IP datagrams when needed.
5. No station shall know anything apart from its own timetable and neighbouring stations.

# Constraints

1. Two implementations of station server in different languages: Java, Python, C xor C++.
2. Employ core networking functions (system calls and standard library) and **not** 3rd party frameworks/resources. Don't use Python's http.server module or C++'s Boost library.
3. Will be marked on macOS or Linux. Indicate which system you used.
