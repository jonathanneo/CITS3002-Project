import socket

HEADER = 64
PORT = 5050
SERVER = socket.gethostbyname(socket.gethostname())
ADDR = (SERVER, PORT)  # Tuple
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "!DISCONNECT"

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(ADDR)


def send(msg):
    message = msg.encode(FORMAT)  # encode the msg string into a byte object
    msg_length = len(message)
    send_length = str(msg_length).encode(FORMAT)
    send_length += b' ' * (HEADER - len(send_length))
    client.send(send_length)
    client.send(message)
    # ideally use same protocol for client -> server send_msg
    print(client.recv(2048).decode(FORMAT))


send("hello world 1!")
send("hello world 2!")
send("hello world 3!")
send(DISCONNECT_MESSAGE)
