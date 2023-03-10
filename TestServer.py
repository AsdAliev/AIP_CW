# pip install opencv-python
import socket, cv2, pickle, struct, imutils
import threading
import pyshine as ps

mode = 'get'
audio_get, context = ps.audioCapture(mode=mode)

mode = 'send'
audio_send, context = ps.audioCapture(mode=mode)

# Socket Create
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
host_ip = '192.168.1.9'
port = 8080
socket_address = (host_ip, port)

# Socket Bind
server_socket.bind(socket_address)

# Socket Listen
server_socket.listen(5)
print("LISTENING AT:", socket_address)

# Socket Accept

client_socket, addr = server_socket.accept()
print('GOT CONNECTION FROM:', addr)

if client_socket:
    vid = cv2.VideoCapture(0)  # Запись видео


def send():
    while vid.isOpened() and client_socket:
        # Send audio
        frame = audio_send.get()
        a = pickle.dumps(frame)
        message = struct.pack("Q", len(a)) + a
        client_socket.sendall(message)
        # Send video
        img, frame = vid.read()
        frame = imutils.resize(frame, width=320)
        a = pickle.dumps(frame)
        message = struct.pack("Q", len(a)) + a
        client_socket.sendall(message)
        cv2.imshow("TRANSMITTING VIDEO", frame)
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            client_socket.close()
            exit(1)


def get():
    data = b""
    payload_size = struct.calcsize("Q")
    # Get audio
    while client_socket:
        while len(data) < payload_size:
            packet = client_socket.recv(4 * 1024)  # 4K
            if not packet:
                break
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
    # Get video
    while vid.isOpened() and client_socket:
        while len(data) < payload_size:
            packet = client_socket.recv(4 * 1024)  # 4K
            if not packet:
                break
            data += packet
        packed_msg_size = data[:payload_size]
        data = data[payload_size:]
        msg_size = struct.unpack("Q", packed_msg_size)[0]
        while len(data) < msg_size:
            data += client_socket.recv(4 * 1024)
        frame_data = data[:msg_size]
        data = data[msg_size:]
        rframe = pickle.loads(frame_data)
        cv2.imshow("RECEIVING VIDEO", rframe)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            client_socket.close()
            exit(1)


t1 = threading.Thread(target=get, args=())
t2 = threading.Thread(target=send, args=())
t1.start()
t2.start()
