import tkinter as tk
from tkinter import filedialog
from PIL import ImageTk, Image

from threading import Thread
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.animation import FuncAnimation
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

import main

PLOT_QUANTITY = 250

def get_yt_video():
    #label.config(text=str(box.get()))
    # yt = YouTube(str(box.get())) 
    # try: 
    #     mp4files = yt.streams.get_highest_resolution()
    #     mp4files.download(output_path="/home/yasmin/Documents/ieee/flashy_images_detection/save_data") 
    # except: 
    #     print("Some Error!") 
    # print('Task Completed!') 
    # main.get_video_brightness(box.get())
    
    # t1 = Thread(target=main.get_video_brightness, args=(box.get(),))
    # t1.daemon = True
    # t1.start()
    pass

def unhide_hide(root):
    main_window.deiconify()
    root.destroy()

def new_window1():
    main_window.withdraw()
    
    root = tk.Toplevel(main_window)
    root.geometry("720x720")
    root.title("Video link")
    root.resizable(True, False)

    
    label1 = tk.Label(root, font=("Ubuntu", 24),  text="Enter a video link")
    label1.pack()
    
    global box
    box = tk.Entry(root, width=40, font=("Ubuntu", 24))
    box.pack(padx=40, pady=50)
    
    buttom = tk.Button(root, font=("Ubuntu", 24),  text='Submit', command=get_yt_video)
    buttom.pack(padx=20, pady=20)
    
    bnt2 = tk.Button(root, font=("Ubuntu", 24), text="Close this window", command=lambda:unhide_hide(root))
    bnt2.pack()

    label = tk.Label(root, text="Realtime Animated Graphs")
    label.pack()
    
    canvas = FigureCanvasTkAgg(plt.gcf(), master=root)
    canvas.get_tk_widget().pack()

    

def new_window2():
    main_window.filename = filedialog.askopenfilename(initialdir="Home/videos/", title="Select a video path", filetypes=[("mp4 files","*.mp4")])
    t1 = Thread(target=main.get_video_brightness, args=(main_window.filename,))
    t1.daemon = True
    t1.start()



def animate(i):
    plotData = main.data[len(main.data)-PLOT_QUANTITY:-1]
    plt.cla()
    plt.plot(plotData, color="b")
    plt.axis([0,PLOT_QUANTITY, 0, PLOT_QUANTITY])



main_window = tk.Tk()

main_window.geometry("878x530")

main_window.title("Epilepsy Alert Project")
label = tk.Label(main_window, font=("Ubuntu", 24), text="Brain Week Project")
label.pack()

bg = ImageTk.PhotoImage(file="background.jpg")

mycanvas = tk.Canvas(main_window, width=878, height=500, bd=0, highlightthickness=0)
mycanvas.pack(fill="both", expand=True)
mycanvas.create_image(0, 0, image=bg, anchor="nw")

#Put buttons on canvas
btn = tk.Button(main_window,font=("Ubuntu", 24), width=15, fg="#336d92",  text="YouTube link", command=new_window1)
#btn.pack(padx=20, pady=20)

btn3 = tk.Button(main_window, font=("Ubuntu", 24), width=15, fg="#336d92", text="Video Path", command=new_window2)
#btn3.pack(padx=20, pady=20)

first_btn = mycanvas.create_window(20, 230, anchor="nw", window=btn)
second_btn = mycanvas.create_window(20, 290,anchor="nw", window=btn3)

ani = FuncAnimation(plt.gcf(), animate, interval=1, blit=False)
main_window.mainloop()