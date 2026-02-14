import os
import cv2
import threading
import time
from datetime import datetime

class Camera:
    def __init__(self, camera_index=0):
        self.cap = cv2.VideoCapture(camera_index)
        if not self.cap.isOpened():
            raise ValueError("Could not open video device")
        
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        self.frame = None
        self.ret = False
        self.running = True
        
        # Recording state
        self.is_recording = False
        self.out = None
        
        # Face detection
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.show_faces = False
        
        # Filter state
        self.filter_mode = "Normal" # Normal, Grayscale, Sepia, Edges, Cartoon, Blur
        
        self.camera_index = camera_index
        self._start_thread()

    @staticmethod
    def list_cameras(max_search=5):
        available_cameras = []
        for i in range(max_search):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                available_cameras.append(i)
                cap.release()
        return available_cameras

    def switch_camera(self, new_index):
        if new_index == self.camera_index:
            return
        
        self.running = False
        if self.thread.is_alive():
            self.thread.join()
            
        self.cap.release()
        self.cap = cv2.VideoCapture(new_index)
        if not self.cap.isOpened():
            # Try to revert to old index
            self.cap = cv2.VideoCapture(self.camera_index)
            raise ValueError(f"Could not open camera {new_index}")
            
        self.camera_index = new_index
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self._start_thread()

    def _start_thread(self):
        self.running = True
        self.thread = threading.Thread(target=self._update, daemon=True)
        self.thread.start()

    def _update(self):
        while self.running:
            self.ret, frame = self.cap.read()
            if self.ret:
                # Apply filter
                frame = self._apply_filter(frame)
                
                # Apply face detection
                if self.show_faces:
                    frame = self._detect_faces(frame)
                
                self.frame = frame
                
                # Write to file if recording
                if self.is_recording and self.out is not None:
                    self.out.write(frame)
            
            time.sleep(0.01)

    def _apply_filter(self, frame):
        if self.filter_mode == "Grayscale":
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            return cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
        
        elif self.filter_mode == "Sepia":
            kernel = cv2.getGaussianKernel(3, 0) # Placeholder for actual sepia matrix logic
            # Simpler sepia implementation
            img_sepia = cv2.transform(frame, cv2.UMat(bytearray([
                0.272, 0.534, 0.131,
                0.349, 0.686, 0.168,
                0.393, 0.769, 0.189
            ])).get().reshape((3, 3)))
            return cv2.convertScaleAbs(img_sepia)

        elif self.filter_mode == "Edges":
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 100, 200)
            return cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
            
        elif self.filter_mode == "Cartoon":
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.medianBlur(gray, 5)
            edges = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 9, 9)
            color = cv2.bilateralFilter(frame, 9, 300, 300)
            cartoon = cv2.bitwise_and(color, color, mask=edges)
            return cartoon
            
        elif self.filter_mode == "Blur":
            return cv2.GaussianBlur(frame, (21, 21), 0)
            
        return frame

    def _detect_faces(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)
        return frame

    def get_frame(self):
        return self.ret, self.frame

    def take_snapshot(self):
        if self.ret and self.frame is not None:
            if not os.path.exists('snapshots'):
                os.makedirs('snapshots')
            filename = f"snapshots/snapshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            cv2.imwrite(filename, self.frame)
            return filename
        return None

    def start_recording(self):
        if not self.is_recording:
            if not os.path.exists('recordings'):
                os.makedirs('recordings')
            filename = f"recordings/video_{datetime.now().strftime('%Y%m%d_%H%M%S')}.avi"
            fourcc = cv2.VideoWriter_fourcc(*'XVID')
            self.out = cv2.VideoWriter(filename, fourcc, 20.0, (self.width, self.height))
            self.is_recording = True
            return filename
        return None

    def stop_recording(self):
        if self.is_recording:
            self.is_recording = False
            if self.out:
                self.out.release()
                self.out = None

    def release(self):
        self.running = False
        if self.is_recording:
            self.stop_recording()
        self.cap.release()
        if self.thread.is_alive():
            self.thread.join()
