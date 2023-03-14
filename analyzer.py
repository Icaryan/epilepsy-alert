import cv2
import numpy as np
import yt_dlp

from multiprocessing import Queue

BRIGHTNESS_THRESHOLD = 20
HZ_THRESHOLD = 3

class analyzer:
    analyzed_data = []    
    frames = []


    def __init__(self, reference:str, quality="144p"):
        self.reference = reference

        if self.reference.startswith('https'):
            self.type = "link"
        else:
            self.type = "path"
        
        self.quality = quality




    def run(self, frames: Queue, dang_secs: Queue):
        ref = ""
        if self.type == "link":
            ytdlp = yt_dlp.YoutubeDL()
            info = ytdlp.extract_info(self.reference, download=False)
            formats = info.get("formats", None)   

            for f in formats:
                if(f.get("format_note", None) == self.quality):
                    ref = f.get("url", None)

        elif self.type == "path":
            ref = self.reference

        self.video = cv2.VideoCapture(ref)
        
        fps = round(self.video.get(cv2.CAP_PROP_FPS))

        data = []

        i = 0
        while self.video.isOpened():
            rtn, frame = self.video.read()
            
            if rtn is not True: break

            self.frames.append(frame)
            frames.put(frame)

            scale_down_factor = 16
            (height, width, _) = frame.shape
            frame = cv2.resize(frame, (height//scale_down_factor, width//scale_down_factor))

            upacked_frame = frame.reshape((height // scale_down_factor * width // scale_down_factor, 3))

            brightness_values = []
            for (blue, green, red) in upacked_frame:
                brightness_values.append(0.0722 * blue + 0.7152 * green + 0.2126 * red)

            avarage_brightness = np.average(brightness_values)
            data.append(avarage_brightness)

            i += 1
            if i % fps == 0:
                self.analyzed_data = self.analyze_brightness(np.array([fps, data], dtype=object))
                
                if len(self.analyzed_data) > 0:
                        dang_secs.put(self.analyzed_data[-1])
        
        self.analyzed_data = self.analyze_brightness(np.array([fps, data], dtype=object))

        dang_secs.put(self.analyzed_data[-1])

        self.video.release()
    

    def analyze_brightness(self, brightness_data:np.ndarray):

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
                if abs(brightness_difference) > BRIGHTNESS_THRESHOLD:
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

            if hz >= HZ_THRESHOLD:
                # print("Warning for the frames {} - {} with {}".format(current_frame, current_frame + fps_rounded, hz))
                dangerous_frames.append(current_frame)
            current_frame += fps_rounded

        # parse to seconds; slightly inaccurate since the fps are rounded; more inaccurate with longer videos
        dangerous_seconds = [x / fps_rounded for x in dangerous_frames]
        return dangerous_seconds
