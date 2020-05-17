import socket
PORT = 6060
SERVER = socket.gethostbyname(socket.gethostname())
serverAddressPort = (SERVER, PORT)

bufferSize = 1024


# Create a UDP socket at client side

UDPClientSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)


# Send to server using created UDP socket

UDPClientSocket.sendto("Hello UDP Server".encode(), serverAddressPort)


msgFromServer = UDPClientSocket.recvfrom(bufferSize)


msg = f"Message from Server {msgFromServer[0]}"

print(msg)
