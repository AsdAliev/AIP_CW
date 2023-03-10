# pip install opencv-python
import socket, cv2, pickle, struct, imutils

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

data = b""
payload_size = struct.calcsize("Q")

if client_socket:
    vid = cv2.VideoCapture(0)  # Запись видео

    while vid.isOpened() and client_socket:
        # Отправка видео
        img, frame = vid.read()
        frame = imutils.resize(frame, width=320)
        a = pickle.dumps(frame)
        message = struct.pack("Q", len(a)) + a
        client_socket.sendall(message)
        cv2.imshow("TRANSMITTING VIDEO", frame)

        # Получение видео и обработка
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
        cv2.imshow("RECEIVING VIDEO", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            client_socket.close()
            exit(1)
