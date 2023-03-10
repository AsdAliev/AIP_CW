# pip install pyshine==0.0.6
import socket, pickle, struct
import pyshine as ps

mode = 'get'
name = 'CLIENT RECEIVING AUDIO'
audio_get, context = ps.audioCapture(mode=mode)

mode = 'send'
name = 'SERVER TRANSMITTING AUDIO'
audio_send, context = ps.audioCapture(mode=mode)

# create socket
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
host_ip = '192.168.1.9'
port = 8080

socket_address = (host_ip, port)
client_socket.connect(socket_address)
print("CLIENT CONNECTED TO", socket_address)

data = b""
payload_size = struct.calcsize("Q")

while True:

    frame = audio_send.get()
    a = pickle.dumps(frame)
    message = struct.pack("Q", len(a)) + a
    client_socket.sendall(message)

    while len(data) < payload_size:
        packet = client_socket.recv(4 * 1024)  # 4K
        if not packet: break
        data += packet
    packed_msg_size = data[:payload_size]
    data = data[payload_size:]
    msg_size = struct.unpack("Q", packed_msg_size)[0]

    while len(data) < msg_size:
        data += client_socket.recv(4 * 1024)
    frame_data = data[:msg_size]
    data = data[msg_size:]
    frame = pickle.loads(frame_data)
    audio_get.put(frame)

client_socket.close()
