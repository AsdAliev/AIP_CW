# pip install opencv-python
import socket, cv2, pickle, struct, imutils
import threading
import pyshine as ps

mode = 'get'
audio_get, context = ps.audioCapture(mode=mode)

mode = 'send'
audio_send, context = ps.audioCapture(mode=mode)

# create socket
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
host_ip = '192.168.1.9'  # Твой IP с помощью ipconfig в cmd
port = 8080
socket_address = (host_ip, port)
client_socket.connect(socket_address)

if client_socket:
    vid = cv2.VideoCapture(0)  # Запись видео


def send_audio():
    data = b""
    payload_size = struct.calcsize("Q")
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


def get_audio():
    frame = audio_send.get()
    a = pickle.dumps(frame)
    message = struct.pack("Q", len(a)) + a
    client_socket.sendall(message)


def send_video():
    while vid.isOpened() and client_socket:
        # Отправка видео
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


def get_video():
    # Получение видео и обработка
    data = b""
    payload_size = struct.calcsize("Q")
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


t1 = threading.Thread(target=get_video, args=())
t2 = threading.Thread(target=send_video, args=())
t3 = threading.Thread(target=get_audio, args=())
t4 = threading.Thread(target=send_audio, args=())
t1.start()
t2.start()
t3.start()
t4.start()
