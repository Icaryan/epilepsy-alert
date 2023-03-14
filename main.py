import cv2
import numpy as np
import yt_dlp
import time
import matplotlib.pyplot as plt

brightness_treshold = 20
hz_treshold = 3

PLOT_QUANTITY = 300

def show_video_brightness(data:np.ndarray):
    plt.ion()
    plt.show()
    plt.cla()

    if(len(data)):
        if(len(data) > PLOT_QUANTITY):
            plotData = data[len(data)-PLOT_QUANTITY:-1]
        else:
            plotData = data
        
        plt.plot(plotData, color='blue')
        plt.axis([0,PLOT_QUANTITY, 0, PLOT_QUANTITY])
        plt.pause(0.010)


def get_video_brightness(video_reference:str):
    """Gets the average brightness from video packets and sends it for analysis

    Args:
        video_reference (str): url to the youtube video
    """
    
    # Exctract the information of possible formats of the video
    ytdl = yt_dlp.YoutubeDL()
    info_dict = ytdl.extract_info(video_reference, download=False)
    formats = info_dict.get("formats", None)

    # With this information gets the url of the worst video format to better prossessing
    url = ""
    for f in formats:
        if f.get("format_note", None) == "144p":
            url = f.get("url", None)
    
    # Initialize the capture of the frames to further analysis
    capture = cv2.VideoCapture(url)
    fps = round(capture.get(cv2.CAP_PROP_FPS))

    # The brightness average and the analyzed data will be stored here
    data = []
    analyzed_data = []

    i = 0
    last_dang_sec = 0

    while capture.isOpened():
        success:bool ; frame:np.ndarray
        success, frame = capture.read()

        if not success: break

        scale_down_factor = 16
        (height, width, _) = frame.shape
        frame = cv2.resize(frame, (width // scale_down_factor, height // scale_down_factor))

        brightness_values = []

        unpacked_frame = frame.reshape((height // scale_down_factor * width // scale_down_factor, 3))

        for (blue, green, red) in unpacked_frame:
            # based on https://en.wikipedia.org/wiki/Relative_luminance
            brightness_values.append(0.0722 * blue + 0.7152 * green + 0.2126 * red)

        average_brightness = np.average(brightness_values)
        data.append(average_brightness)

        i += 1

        if i % fps == 0:
            # print("{} Frames to analyze".format(len(data)))

            analyzed_data = analyze_brightness(np.array([fps, data], dtype=object))
            if len(analyzed_data) > 1:
                if last_dang_sec != analyzed_data[-1]:
                    last_dang_sec = analyzed_data[-1]
                    print("Last Dangerous second: {}".format(analyzed_data[-1]))
        
        show_video_brightness(data)

    analyzed_data = analyze_brightness(np.array([fps, data], dtype=object))
    # print(analyzed_data)

    capture.release()

def analyze_brightness(brightness_data:np.ndarray):

    (fps, data) = brightness_data

    fps_rounded = round(fps)
    frame_count = len(data)

    # Avoiding an array out of bounds when the video doesn't end on an exact second
    last_frames_amount = frame_count % fps_rounded
    if last_frames_amount == 0:
        last_frames_amount = fps_rounded
    end_frame = frame_count - last_frames_amount

    current_frame = 0
    # was it getting darker or brighter? 0 - undefined; 1 - brighter; -1 - darker
    # needed to not count every monotone change as an hz; i.e. +20 to another +20 as 2 hz
    current_direction = 0

    dangerous_frames = []

    # approximately one second is being viewed here
    while current_frame < end_frame - fps_rounded:
        # initializes the frames of the seconds and set's the reference frame to the first one in this set
        current_view = data[current_frame:current_frame + fps_rounded]
        current_reference_frame = current_view[0]

        # keeps track of the measured hz
        hz = 0

        # keeps track of not overstepping the second
        i = 0

        # every frame in this second is being viewed here
        while i < fps_rounded:

            brightness_difference = current_reference_frame - current_view[i]
            if abs(brightness_difference) > brightness_treshold:
                if (brightness_difference // abs(brightness_difference)) == current_direction:
                    # If the brightness threshold is exceeded but in the same direction, just update the reference frame
                    current_reference_frame = current_view[i]
                else:
                    # If the brightness threshold is exceeded in another direction than previously count it as an hz and update the reference_frame
                    hz += 1
                    current_reference_frame = current_view[i]
                    # No direction of the light has been set; so it will assigne one if this condition is true
                    # It shouldn't become zero again; since it takes the direction from previous frame-second-sets
                    if current_direction == 0:
                        if (current_view[i] - current_reference_frame) > 0:
                            current_direction = 1
                        else:
                            current_direction = -1
                    # Changing directon to the opposite
                    else:
                        current_direction *= -1
            i += 1

        if hz >= hz_treshold:
            # print("Warning for the frames {} - {} with {}".format(current_frame, current_frame + fps_rounded, hz))
            dangerous_frames.append(current_frame)
        current_frame += fps_rounded

    # parse to seconds; slightly inaccurate since the fps are rounded; more inaccurate with longer videos
    dangerous_seconds = [x / fps_rounded for x in dangerous_frames]
    return dangerous_seconds


if __name__ == "__main__":  
    # url = "https://www.youtube.com/watch?v=ZjdrMuKpaCI"
    # url = "https://www.youtube.com/watch?v=sYvxz9JFp-4"
    # url = "https://www.youtube.com/watch?v=nn2Je5dXpZ8&ab_channel=TheDerpyWhale"
    url = "https://www.youtube.com/watch?v=71-tMMtVWMI"
    
    start = time.time()

    get_video_brightness(url)
    
    print("Elepsed time: {}".format(+ time.time() - start))
