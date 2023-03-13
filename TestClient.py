import socket, cv2, pickle, struct, imutils
import pyshine as ps
import threading


def audio_stream():
    # Socket Create
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    host_ip = '192.168.1.9'
    port = 8080

    socket_address = (host_ip, port)
    client_socket.connect(socket_address)
    print("CLIENT CONNECTED TO", socket_address)

    mode = 'get'
    audio_get, context = ps.audioCapture(mode=mode)

    data = b""
    payload_size = struct.calcsize("Q")
    while True:
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


def video_stream():
    # Socket Create
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    host_ip = '192.168.1.9'
    port = 8080

    socket_address = (host_ip, port-1)
    client_socket.connect(socket_address)
    print("CLIENT CONNECTED TO", socket_address)

    if client_socket:
        vid = cv2.VideoCapture(0)  # Запись видео

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
            frame = pickle.loads(frame_data)
            cv2.imshow("RECEIVING VIDEO", frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                client_socket.close()
                exit(1)


t1 = threading.Thread(target=audio_stream, args=())
t2 = threading.Thread(target=video_stream, args=())
t1.start()
t2.start()
