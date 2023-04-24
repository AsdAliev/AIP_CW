from tkinter import *
from tkinter import messagebox
from Server import *
import threading


def on_closing():
    global STOP
    if messagebox.askokcancel("Quit", "Do you want to quit?"):
        window.destroy()
        STOP = True
        print("Closing the programme...")
        event_record.set()
        event_video.set()




def record_thread():
    global STOP
    while not STOP:
        event_record.wait()
        while event_record.is_set() and not STOP:
            send_audio()


def stop_record():
    event_record.clear()


def start_record():
    event_record.set()


def play_thread():
    global STOP
    while not STOP:
        if not event_play.is_set() or STOP:
            client_socket_audio.recv(CHUNK_SIZE)
        while event_play.is_set() and not STOP:
            receive_audio()


def stop_play():
    event_play.clear()


def start_play():
    event_play.set()


def video_thread():
    global STOP
    while not STOP:
        event_video.wait()
        vid = cv2.VideoCapture(0)
        while event_video.is_set() and not STOP:
            video_stream(vid)
        vid.release()
        cv2.destroyAllWindows()


def stop_video():
    event_video.clear()


def start_video():
    event_video.set()


STOP = False

event_record = threading.Event()
event_play = threading.Event()
event_video = threading.Event()
t_record = threading.Thread(target=record_thread, args=())
t_play = threading.Thread(target=play_thread, args=())
t_video = threading.Thread(target=video_thread, args=())
t_record.start()
t_play.start()
t_video.start()

window = Tk()
window.title("Robot control")
window.geometry('400x250')

btn_record = Button(window, text="Начать запись", command=start_record)
btn_record.grid(column=0, row=0)

btn_stop_rec = Button(window, text="Остановить запись", command=stop_record)
btn_stop_rec.grid(column=1, row=0)

btn_play = Button(window, text="Начать проигрывание", command=start_play)
btn_play.grid(column=0, row=1)

btn_stop_play = Button(window, text="Остановить проигрывание", command=stop_play)
btn_stop_play.grid(column=1, row=1)

btn_video = Button(window, text="Начать видео", command=start_video)
btn_video.grid(column=0, row=2)

btn_stop_video = Button(window, text="Остановить видео", command=stop_video)
btn_stop_video.grid(column=1, row=2)

window.protocol("WM_DELETE_WINDOW", on_closing)
window.mainloop()
