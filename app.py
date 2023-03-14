import tkinter as tk
from tkinter import filedialog

from PIL import Image, ImageTk
import yt_dlp
import cv2

from multiprocessing import Process, Queue

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)

import analyzer

qtt_frame = 0
duration = 0
pos = [0]

def get_worst_url(video_reference):
    ytdl = yt_dlp.YoutubeDL()
    info_dict = ytdl.extract_info(video_reference, download=False)
    formats = info_dict.get("formats", None)

    # With this information gets the url of the worst video format to better prossessing
    url = ""
    for f in formats:
        if f.get("format_note", None) == "144p":
            url = f.get("url", None)
    
    return url



def show_video(video, lbl, cnv, rect, delay):
    global qtt_frame
    
    qtt_frame = qtt_frame + 1

    try:
        _, frame = video.read()
        cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
        img = Image.fromarray(cv2image)
        img = img.resize((720, 380))
        imgTk = ImageTk.PhotoImage(image=img)

        lbl.config(image = imgTk)
        lbl.image = imgTk
        lbl.after(delay, lambda: show_video(video, lbl, cnv, rect, delay))
        
        cnv.coords(rect, 0,0,720/(duration*30)*qtt_frame,10)
    except:
        return



def show_frames(frames, dang_secs, lbl, cnv, rect, delay):
    global qtt_frame

    if frames.qsize() > delay * 5:
        cv2image = cv2.cvtColor(frames.get(), cv2.COLOR_BGR2RGBA)
        img = Image.fromarray(cv2image)
        img = img.resize((int(cnv.winfo_screenwidth()*0.7), int(cnv.winfo_screenheight()*0.7)))
        imgTk = ImageTk.PhotoImage(image=img)

        lbl.config(image = imgTk)
        lbl.image = imgTk
        
        cnv.coords(rect, 0,20, int(cnv.winfo_screenwidth()*0.7)/(duration*fps)*qtt_frame, fps)

        qtt_frame += 1

    if dang_secs.qsize() > 0:
        position_scale = cnv.winfo_screenwidth()*0.7/(duration)

        sec = dang_secs.get()
        if sec not in pos:
            print(sec)
            pos.append(sec)
        
        cnv.create_oval(position_scale*pos[-1], 0, position_scale*pos[-1]+10, 10, fill="blue")

    lbl.after(delay, lambda: show_frames(frames, dang_secs, lbl, cnv, rect, delay))



def get_video_link(last_frame):
    last_frame.destroy()

    frm_main = tk.Frame(window, width=300, height=480, bg="#000C66")
    frm_main.pack_propagate(False)
    frm_main.pack(fill="both", side="right", padx=10, pady=10)

    lbl_opcao = tk.Label(frm_main, fg="white", bg=frm_main['background'], font=("Roboto",16), text="Brain Week")
    lbl_opcao.pack(pady=(150,10))

    lbl_link = tk.Label(frm_main, text="Paste video link:", fg="white", bg=frm_main["background"], font=("Roboto", 12))
    lbl_link.pack(padx=10, pady=10, anchor="nw")

    frm_link = tk.Frame(frm_main, bg=frm_main["background"])
    frm_link.pack()

    etr_link = tk.Entry(frm_link, width=30)
    etr_link.pack(side="left", padx=10)

    btn_submit = tk.Button(frm_link, text="Submit", font=("Roboto", 10), command=lambda: analyze_video(etr_link.get()))
    btn_submit.pack(side="right", padx=10, ipadx=5)

    btn_back = tk.Button(frm_main, text="Back", command=lambda: init_frame(frm_main))
    btn_back.pack(side="top", pady=20, ipadx=5)



def analyze_video(reference):
    global procs
    global duration

    if(len(reference) <= 0):
        return

    anl = analyzer.analyzer(reference, "360p")

    frames = Queue()
    dang_secs = Queue()
    brightness = Queue()

    procs = []
    proc = Process(target=anl.run, args=(frames, dang_secs, brightness,))
    procs.append(proc)
    proc.start()
    
    root = tk.Toplevel(window)
    
    width = 1080
    height = 720
    
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    
    x = (screen_width/2) - (width/2)
    y = (screen_height/2) - (height/2)
    
    root.geometry('%dx%d+%d+%d' % (width, height, x, y))

    
    f1 = tk.Frame(root)
    l1 = tk.Label(f1)
    c1 = tk.Canvas(f1, width=int(root.winfo_screenwidth()*0.7), height=50, background="gray")
    rect = c1.create_rectangle(0,0,0,10,fill="red")

    l1.pack()
    f1.pack()
    c1.pack()

    if anl.type == "link":
        video = cv2.VideoCapture(get_worst_url(reference))
    
    elif anl.type == "path":
        video = cv2.VideoCapture(reference)

    global fps
    global delay
    fps = video.get(cv2.CAP_PROP_FPS)
    delay = int(video.get(cv2.CAP_PROP_FPS) / 2)
    duration = video.get(cv2.CAP_PROP_FRAME_COUNT) / (delay * 2)

    global pos
    global qtt_frame
    pos = [0]
    qtt_frame = 0
    show_frames(frames, dang_secs, l1, c1, rect, delay)
    
    show_luminance_history(brightness)

    window.withdraw()

    # print(spix_read())

    root.wait_window()

    video.release()
    window.deiconify()
    root.destroy()
    
    for p in procs:
        p.terminate()



def get_video_path():
    file_path = filedialog.askopenfilename(title="Select a video path", filetypes=[("mp4 files","*.mp4")])
    
    analyze_video(file_path)



def init_frame(last_frame=None):
    if last_frame is not None:
        last_frame.destroy()

    frm_main = tk.Frame(window, width=300, height=480, bg="#000C66")
    frm_main.pack_propagate(False)
    frm_main.pack(fill="both", side="right", padx=10, pady=10)

    lbl_opcao = tk.Label(frm_main, fg="white", bg=frm_main['background'], font=("Roboto",16), text="Brain Week")
    lbl_opcao.pack(pady=(150,10))
    
    btn_link = tk.Button(frm_main, width=15, font=("Roboto",12), text="Video Link", command=lambda: get_video_link(frm_main))
    btn_link.pack(pady=10)

    btn_path = tk.Button(frm_main, width=15, font=("Roboto",12), text="Video Path", command=lambda: get_video_path())
    btn_path.pack(pady=10)



def show_luminance_history(brightness ):
    root = tk.Toplevel(window)
    
    width = 1080
    height = 720
    
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    
    x = (screen_width/2) - (width/2)
    y = (screen_height/2) - (height/2)
    
    root.geometry('%dx%d+%d+%d' % (width, height, x, y))

    fig = Figure(figsize = (5, 5), dpi = 100)
    plot1 = fig.add_subplot(111)

    canvas = FigureCanvasTkAgg(fig, master = root)  
    canvas.draw()

    canvas.get_tk_widget().pack()

    toolbar = NavigationToolbar2Tk(canvas, root)
    toolbar.update()

    canvas.get_tk_widget().pack()

    global datas
    datas = []

    show_plot(brightness, plot1, canvas, root)


def show_plot(brightness , plot1, canvas, root):
    
    if brightness.qsize() > 0:
        data = brightness.get()
        if data not in datas:
            datas.append(data)
            
            if len(datas) % int(fps) == 0:
                plot1.cla()
                
                if len(datas) > 300:
                    plot1.plot(datas[len(datas)-300:-1], color="blue")
                else:
                    plot1.plot(datas, color="blue")

                plot1.axis([0, 300, 0, 300])
                canvas.draw()
                
    root.after(1, lambda: show_plot(brightness, plot1, canvas, root))
        


def spix_read():
    import pyaudio

    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 2
    RATE = 44100
    RECORD_SECONDS = 5
    WAVE_OUTPUT_FILENAME = "output.wav"
    
    p = pyaudio.PyAudio()
    stream = p.open(
                format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK)
    
    frames = []

    for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
        data = stream.read(CHUNK)
    frames.append(data)

    stream.stop_stream()
    stream.close()
    p.terminate()

    return frames



if __name__ == "__main__":
    url_test = [
        "https://www.youtube.com/watch?v=FXqp9WiFWzc"
    ]

    global window

    window = tk.Tk()

    window.title("Epilepsy Alert Project")
    window.config(bg="black")
    
    width = 720
    height = 480
    
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    
    x = (screen_width/2) - (width/2)
    y = (screen_height/2) - (height/2)
    
    window.geometry('%dx%d+%d+%d' % (width, height, x, y))


    img = Image.open("background.jpg")
    img = img.resize((round(img.width/3), round(img.height/3)))
    imgtk = ImageTk.PhotoImage(image=img)

    lbl_img = tk.Label(window, width=420, image=imgtk, background="black")
    lbl_img.pack(side="left")

    init_frame()

    window.mainloop()
