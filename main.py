import cv2
import tkinter as tk

class App:
    def __init__(self, window, window_title):
        self.window = window
        self.window.title(window_title)
        
        # Create a button for starting and stopping the video capture
        self.btn_start_stop = tk.Button(window, text="Start", width=50, command=self.start_stop)
        self.btn_start_stop.pack(padx=10, pady=10)
        
        # Create a label for displaying the video
        self.label = tk.Label(window)
        self.label.pack()
        
        # Set up the video capture
        self.cap = cv2.VideoCapture(0)
        self.out = cv2.VideoWriter('output.avi', cv2.VideoWriter_fourcc(*'MJPG'), 30, (640,480))
        
        # Start the GUI event loop
        self.window.mainloop()
        
    def start_stop(self):
        if self.btn_start_stop["text"] == "Start":
            self.btn_start_stop["text"] = "Stop"
            self.video_loop()
        else:
            self.btn_start_stop["text"] = "Start"
            self.cap.release()
            self.out.release()
            self.label.config(image='')
        
    def video_loop(self):
        ret, frame = self.cap.read()
        if ret:
            self.out.write(frame)
            cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
            img = Image.fromarray(cv2image)
            imgtk = ImageTk.PhotoImage(image=img)
            self.label.imgtk = imgtk
            self.label.config(image=imgtk)
            self.window.after(10, self.video_loop)

# Create the GUI window
window = tk.Tk()

# Create an instance of the App class
app = App(window, "Webcam Video Capture")
