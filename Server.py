import socket
import cv2
import pickle
import struct
import imutils
import threading
import pyaudio

# Initialize PyAudio and constants
VIDEO_SIZE = 512
CHUNK_SIZE = 600
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
p = pyaudio.PyAudio()

# Open microphone stream
stream_in = p.open(format=FORMAT, channels=CHANNELS, rate=RATE,
                   input=True, frames_per_buffer=CHUNK_SIZE)

# Open speaker stream
stream_out = p.open(format=FORMAT, channels=CHANNELS, rate=RATE,
                    output=True, frames_per_buffer=CHUNK_SIZE)

HOST_IP = '192.168.1.9'  # ip from ipconfig
PORT = 8080  # Any port

# Socket Create
server_socket_audio = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
backlog = 5
socket_address_audio = (HOST_IP, PORT)
print('STARTING SERVER AT', socket_address_audio, '...')
server_socket_audio.bind(socket_address_audio)
server_socket_audio.listen(backlog)

client_socket_audio, addr_audio = server_socket_audio.accept()
print('GOT (audio) CONNECTION FROM:', addr_audio)


def send_audio():
    while True:
        # Read audio data from the microphone stream
        data = stream_in.read(CHUNK_SIZE)
        # Send audio data to the client
        client_socket_audio.sendall(data)


def receive_audio():
    while True:
        # Receive audio data from the server
        data = client_socket_audio.recv(CHUNK_SIZE)
        # Play audio data on the speaker stream
        stream_out.write(data)


def video_stream():
    # Socket Create
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    socket_address = (HOST_IP, PORT - 1)
    server_socket.bind(socket_address)
    server_socket.listen(5)
    print("LISTENING AT:", socket_address)

    # Socket Accept
    client_socket, addr = server_socket.accept()
    print('GOT (video) CONNECTION FROM:', addr)

    print("Enter 'q' to close program")

    data = b""
    payload_size = struct.calcsize("Q")
    if client_socket:
        vid = cv2.VideoCapture(0)  # Recording video

        while vid.isOpened() and client_socket:
            # Receive video
            while len(data) < payload_size:
                packet = client_socket.recv(VIDEO_SIZE)
                if not packet:
                    break
                data += packet
            packed_msg_size = data[:payload_size]
            data = data[payload_size:]
            msg_size = struct.unpack("Q", packed_msg_size)[0]
            while len(data) < msg_size:
                data += client_socket.recv(VIDEO_SIZE)
            frame_data = data[:msg_size]
            data = data[msg_size:]
            frame = pickle.loads(frame_data)
            cv2.imshow("RECEIVING VIDEO", frame)
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
                print("You entered 'q'")
                exit(1)


t1 = threading.Thread(target=send_audio, args=())
t2 = threading.Thread(target=receive_audio, args=())
t3 = threading.Thread(target=video_stream, args=())
t1.start()
t2.start()
t3.start()
