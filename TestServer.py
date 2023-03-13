import socket, cv2, pickle, struct, imutils
import pyshine as ps
import threading


def audio_stream():
    # Socket Create
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    host_ip = '192.168.1.9'
    port = 8080
    backlog = 5
    socket_address = (host_ip, port)
    print('STARTING SERVER AT', socket_address, '...')
    server_socket.bind(socket_address)
    server_socket.listen(backlog)

    client_socket, addr = server_socket.accept()
    print('GOT (audio) CONNECTION FROM:', addr)

    mode = 'send'
    audio_send, context = ps.audioCapture(mode=mode)

    while True:
        frame = audio_send.get()
        a = pickle.dumps(frame)
        message = struct.pack("Q", len(a)) + a
        client_socket.sendall(message)


def video_stream():
    # Socket Create
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    host_ip = '192.168.1.9'
    port = 8080
    socket_address = (host_ip, port-1)
    server_socket.bind(socket_address)
    server_socket.listen(5)
    print("LISTENING AT:", socket_address)

    # Socket Accept

    client_socket, addr = server_socket.accept()
    print('GOT (video) CONNECTION FROM:', addr)

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

            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                client_socket.close()
                exit(1)


t1 = threading.Thread(target=audio_stream, args=())
t2 = threading.Thread(target=video_stream, args=())
t1.start()
t2.start()
