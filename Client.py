import socket
import cv2
import pickle
import struct
import imutils
import threading
import pyaudio
import numpy as np
from scipy.signal import butter, filtfilt

# Initialize PyAudio and constants
VIDEO_SIZE = 512
CHUNK_SIZE = 5000
FORMAT = pyaudio.paInt16
CUTOFF_FREQ = 5000
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
client_socket_audio = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
socket_address_audio = (HOST_IP, PORT)
client_socket_audio.connect(socket_address_audio)
print("CLIENT CONNECTED TO", socket_address_audio)


def low_pass_filter(data, cutoff_freq, sample_rate):
    # Преобразование байт в массив чисел
    data = np.frombuffer(data, dtype=np.int16)

    # Нормализация данных
    data_norm = data / (2 ** 15)

    # Расчет параметров фильтра
    nyquist_freq = 0.5 * sample_rate
    normal_cutoff_freq = cutoff_freq / nyquist_freq
    order = 5

    # Создание фильтра Butterworth
    b, a = butter(order, normal_cutoff_freq, btype='lowpass', analog=False)

    # Фильтрация данных
    data_filtered = filtfilt(b, a, data_norm)

    # Нормализация отфильтрованных данных
    data_filtered_norm = data_filtered * (2 ** 15)

    # Преобразование отфильтрованных данных в байты
    data_filtered_bytes = data_filtered_norm.astype(np.int16).tobytes()

    return data_filtered_bytes


def band_pass_filter(data, sample_rate, lowcut, highcut):
    nyquist_rate = sample_rate / 2
    low = lowcut / nyquist_rate
    high = highcut / nyquist_rate
    order = 5
    b, a = butter(order, [low, high], btype='band', analog=False)
    y = np.frombuffer(data, dtype='int16')
    filtered_y = filtfilt(b, a, y)
    filtered_data = filtered_y.astype('int16').tobytes()
    return filtered_data


def send_audio():
    while True:
        if client_socket_audio:
            # Read audio data from the microphone stream
            data = stream_in.read(CHUNK_SIZE)
            # Send audio data to the client
            client_socket_audio.sendall(data)
        else:
            break


def receive_audio():
    while True:
        if client_socket_audio:
            # Receive audio data from the server
            data = client_socket_audio.recv(CHUNK_SIZE)

            data_for_commands = band_pass_filter(data, RATE, 6900, 7100)

            data = low_pass_filter(data, CUTOFF_FREQ, RATE)

            # Play audio data on the speaker stream
            stream_out.write(data)
        else:
            break


def video_stream():
    # Socket Create
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    socket_address = (HOST_IP, PORT-1)
    client_socket.connect(socket_address)
    print("CLIENT CONNECTED TO", socket_address)

    print("Enter 'q' to close program")
    if client_socket:
        vid = cv2.VideoCapture(0)  # Запись видео

        data = b""
        payload_size = struct.calcsize("Q")
        while vid.isOpened():
            if client_socket:
                # Send video
                img, frame = vid.read()
                frame = imutils.resize(frame, width=320)
                a = pickle.dumps(frame)
                message = struct.pack("Q", len(a)) + a
                client_socket.sendall(message)
                cv2.imshow("TRANSMITTING VIDEO", frame)
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

                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    client_socket.close()
                    print("You entered 'q'")
                    exit(1)
            else:
                break


t1 = threading.Thread(target=receive_audio, args=())
t2 = threading.Thread(target=send_audio, args=())
t3 = threading.Thread(target=video_stream, args=())
t1.start()
t2.start()
t3.start()
