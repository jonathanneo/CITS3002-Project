import socket
import selectors
import types


class ServerConfig:
    def __init__(self, tcp_port, udp_port, server, format):
        self.HEADER = 64
        self.TCP_PORT = tcp_port
        self.UDP_PORT = udp_port
        self.SERVER = server
        self.TCP_ADDR = (self.SERVER, self.TCP_PORT)
        self.UDP_ADDR = (self.SERVER, self.UDP_PORT)
        self.FORMAT = format
        self.DISCONNECT_MESSAGE = "!DISCONNECT"


def handleTcpClient(serverConfig, conn, addr):
    print(f"[NEW CONNECTION] {addr} connected.")
    connected = True
    while connected:
        # conn.recv(serverConfig.HEADER).decode(serverConfig.FORMAT)
        # Receive 1024 bytes at a time
        msg = conn.recv(1024).decode(serverConfig.FORMAT)
        # if conn.recv() returns an empty bytes object b'' , then terminate the loop
        if not msg:
            connected = False
        pieces = msg.split("\n")
        if (len(pieces) > 0):
            print(pieces[0])
        data = "HTTP/1.1 200 OK\r\n"
        data += "Content-Type: text/html; charset=utf-8\r\n"
        data += "\r\n"
        data += f"<html><body>Hello {addr}!</body></html>\r\n\r\n"
        conn.send(data.encode())
        connected = False
    conn.close()


def accept_tcp_wrapper(sock, sel):
    conn, addr = sock.accept()  # Should be ready to read
    print('accepted connection from', addr)
    conn.setblocking(False)
    # create a data object that holds addr, inb and outb
    data = types.SimpleNamespace(addr=addr, inb=b'', outb=b'')
    events = selectors.EVENT_READ | selectors.EVENT_WRITE
    # register the client socket
    sel.register(conn, events, data=data)


def service_tcp_connection(key, mask, sel):
    connected = True
    sock = key.fileobj
    data = key.data
    # if the socket is ready for reading -- mask is True & selectors.EVENT_READ is True
    if mask & selectors.EVENT_READ:
        # receive the data
        recv_data = sock.recv(1024)
        if recv_data:  # if recv_data is not None
            data.outb += recv_data  # append received data to data.outb
        else:  # the client has closed their socket so the server should too.
            print('closing connection to', data.addr)
            sel.unregister(sock)
            sock.close()
    if mask & selectors.EVENT_WRITE:  # write the data back to the client
        if data.outb and connected:
            # print('echoing', repr(data.outb), 'to', data.addr)
            # sent = sock.send(data.outb)  # send data back to the client
            # data.outb = data.outb[sent:]  # remove sent data from data.outb
            sendData = "HTTP/1.1 200 OK\r\n"
            sendData += "Content-Type: text/html; charset=utf-8\r\n"
            sendData += "\r\n"
            sendData += f"<html><body>Hello {data.addr}!</body></html>\r\n\r\n"
            sock.send(sendData.encode())
            connected = False
            sock.close()


def startTcpUdpPort(serverConfig):
    # create selector
    sel = selectors.DefaultSelector()

    # create TCP server socket
    tcpServerSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcpServerSocket.bind(serverConfig.TCP_ADDR)
    print(serverConfig.TCP_ADDR)
    tcpServerSocket.listen()
    print(f"[LISTENING] TCP Server is listening on {serverConfig.TCP_ADDR}.")
    tcpServerSocket.setblocking(False)
    sel.register(tcpServerSocket, selectors.EVENT_READ, data=None)

    # create UDP server socket
    udpServerSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udpServerSocket.bind(serverConfig.UDP_ADDR)
    print(f"[LISTENING] UDP Server is listening on {serverConfig.UDP_ADDR}.")
    sel.register(udpServerSocket, selectors.EVENT_READ, data=None)

    # wait for connection
    while True:
        # wait unitl registered file objects become ready and set a selector with no timeout
        # the call will block until file object becomes ready -- either TCP or UDP has an EVENT_READ
        events = sel.select(timeout=None)

        for key, mask in events:
            print(f"the key is: {key}.")
            print(f"the sockname is: {key.fileobj.getsockname()}.")
            print(f"the mask is: {mask}.")

            # a listening socket that hasn't been accepted yet i.e. no data
            if key.data is None:

                # if the listening socket is TCP
                if key.fileobj.getsockname() == serverConfig.TCP_ADDR:
                    print("TCP accept wrapper!")
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
                    print("TCP service connection!")
                    service_tcp_connection(key, mask, sel)

        # conn, addr = tcpServerSocket.accept()  # accept new connection
        # handleTcpClient(serverConfig, conn, addr)


def startUdpPort(serverConfig):
    udpServerSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udpServerSocket.bind(serverConfig.UDP_ADDR)
    print(f"[LISTENING] UDP Server is listening on {serverConfig.UDP_ADDR}.")
    while True:
        bytesAddressPair = udpServerSocket.recvfrom(1024)
        message = bytesAddressPair[0]
        address = bytesAddressPair[1]
        clientMsg = f"Message from Client:{message}"
        clientIP = f"Client IP Address:{address}"
        print(clientMsg)
        print(clientIP)
        udpServerSocket.sendto("Hello from server.".encode(), address)


def main():
    tcp_port = 5050
    udp_port = 6060
    server = socket.gethostbyname(socket.gethostname())
    format = 'utf-8'
    serverConfig = ServerConfig(tcp_port, udp_port, server, format)
    # Start TCP port
    startTcpUdpPort(serverConfig)

    # Read CSV timetable file -- assume that all contents are correct

    return None


if __name__ == "__main__":
    main()
