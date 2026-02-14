import tkinter as tk
from tkinter import ttk, messagebox
import cv2
from PIL import Image, ImageTk
from camera import Camera
import os

class WebcamProApp:
    def __init__(self, window):
        self.window = window
        self.window.title("Webcam Pro - Advanced Capture")
        self.window.geometry("1100x750")
        self.window.configure(bg="#2c3e50")
        
        # Initialize camera
        try:
            self.cameras = Camera.list_cameras()
            if not self.cameras:
                messagebox.showerror("Error", "No cameras detected.")
                self.window.destroy()
                return
            self.camera = Camera(self.cameras[0])
        except Exception as e:
            messagebox.showerror("Error", str(e))
            self.window.destroy()
            return
            
        self.setup_ui()
        self.update_loop()
        
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)

    def setup_ui(self):
        # Apply dark theme styles
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Color Palette
        bg_col = "#2c3e50"
        fg_col = "#ecf0f1"
        accent_col = "#3498db"
        danger_col = "#e74c3c"
        success_col = "#2ecc71"

        self.style.configure("TFrame", background=bg_col)
        self.style.configure("TLabel", background=bg_col, foreground=fg_col, font=("Segoe UI", 10))
        self.style.configure("Title.TLabel", font=("Segoe UI", 16, "bold"))
        self.style.configure("Header.TLabel", font=("Segoe UI", 12, "bold"))
        
        self.style.configure("TButton", font=("Segoe UI", 10), padding=5)
        self.style.configure("Action.TButton", background=accent_col, foreground=fg_col)
        self.style.configure("Record.TButton", background=danger_col, foreground=fg_col)
        self.style.configure("Photo.TButton", background=success_col, foreground=fg_col, font=("Segoe UI", 12, "bold"))
        
        self.style.configure("TRadiobutton", background=bg_col, foreground=fg_col)
        self.style.configure("TCheckbutton", background=bg_col, foreground=fg_col)
        
        # Main container
        self.main_frame = ttk.Frame(self.window)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Sidebar for controls
        self.sidebar = ttk.Frame(self.main_frame, width=280)
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 15))
        self.sidebar.pack_propagate(False) # Maintain width
        
        # Video Display Area
        self.display_frame = ttk.Frame(self.main_frame)
        self.display_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        self.canvas = tk.Canvas(self.display_frame, bg="black", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Sidebar Widgets
        ttk.Label(self.sidebar, text="WEBCAM PRO", style="Title.TLabel").pack(pady=(0, 20))
        
        # Camera Selection
        ttk.Label(self.sidebar, text="Select Device:", style="Header.TLabel").pack(anchor=tk.W, pady=(0, 5))
        self.camera_var = tk.StringVar(value=f"Camera {self.cameras[0]}")
        camera_names = [f"Camera {i}" for i in self.cameras]
        self.camera_combo = ttk.Combobox(self.sidebar, textvariable=self.camera_var, values=camera_names, state="readonly")
        self.camera_combo.pack(fill=tk.X, pady=(0, 20))
        self.camera_combo.bind("<<ComboboxSelected>>", self.on_camera_change)

        # Quick Actions
        ttk.Label(self.sidebar, text="Quick Actions:", style="Header.TLabel").pack(anchor=tk.W, pady=(0, 10))
        
        # Large "Take Photo" Button
        self.btn_photo = ttk.Button(self.sidebar, text="📸 TAKE PHOTO", style="Photo.TButton", command=self.take_snapshot)
        self.btn_photo.pack(fill=tk.X, pady=(0, 10))
        
        # Recording Button
        self.btn_rec = ttk.Button(self.sidebar, text="🔴 START RECORDING", style="TButton", command=self.toggle_recording)
        self.btn_rec.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Separator(self.sidebar, orient='horizontal').pack(fill=tk.X, pady=15)
        
        # Filters Section
        ttk.Label(self.sidebar, text="Filters:", style="Header.TLabel").pack(anchor=tk.W, pady=(0, 10))
        
        self.filter_var = tk.StringVar(value="Normal")
        filter_options = ["Normal", "Grayscale", "Sepia", "Edges", "Cartoon", "Blur"]
        
        for f in filter_options:
            ttk.Radiobutton(self.sidebar, text=f, variable=self.filter_var, value=f, command=self.change_filter).pack(anchor=tk.W, pady=2)
            
        ttk.Separator(self.sidebar, orient='horizontal').pack(fill=tk.X, pady=15)
        
        # Features Section
        ttk.Label(self.sidebar, text="Advanced:", style="Header.TLabel").pack(anchor=tk.W, pady=(0, 10))
        
        self.face_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(self.sidebar, text="Enable Face Tracking", variable=self.face_var, command=self.toggle_faces).pack(anchor=tk.W)
        
        # Status Bar
        self.status_label = ttk.Label(self.window, text="Ready", relief=tk.SUNKEN, anchor=tk.W)
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X)

    def on_camera_change(self, event):
        selection = self.camera_var.get()
        idx = int(selection.split()[-1])
        try:
            self.camera.switch_camera(idx)
            self.status_label.config(text=f"Switched to {selection}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to switch camera: {e}")

    def update_loop(self):
        ret, frame = self.camera.get_frame()
        if ret:
            # Convert OpenCV frame (BGR) to RGB for PIL
            cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(cv2image)
            
            # Resize image to fit canvas while maintaining aspect ratio
            canvas_w = self.canvas.winfo_width()
            canvas_h = self.canvas.winfo_height()
            
            if canvas_w > 1 and canvas_h > 1:
                # Maintain aspect ratio
                img_w, img_h = img.size
                ratio = min(canvas_w / img_w, canvas_h / img_h)
                new_size = (int(img_w * ratio), int(img_h * ratio))
                img = img.resize(new_size, Image.Resampling.LANCZOS)
                
            imgtk = ImageTk.PhotoImage(image=img)
            self.canvas.delete("all")
            self.canvas.create_image(canvas_w//2, canvas_h//2, anchor=tk.CENTER, image=imgtk)
            self.canvas.imgtk = imgtk # Keep reference
            
        self.window.after(15, self.update_loop)

    def toggle_recording(self):
        if not self.camera.is_recording:
            filename = self.camera.start_recording()
            if filename:
                self.btn_rec.config(text="⏹ STOP RECORDING")
                self.status_label.config(text=f"Recording to {os.path.basename(filename)}...")
        else:
            self.camera.stop_recording()
            self.btn_rec.config(text="🔴 START RECORDING")
            self.status_label.config(text="Recording saved.")

    def take_snapshot(self):
        filename = self.camera.take_snapshot()
        if filename:
            self.status_label.config(text=f"Photo saved: {os.path.basename(filename)}")

    def change_filter(self):
        self.camera.filter_mode = self.filter_var.get()
        self.status_label.config(text=f"Filter applied: {self.filter_var.get()}")

    def toggle_faces(self):
        self.camera.show_faces = self.face_var.get()
        state = "Enabled" if self.face_var.get() else "Disabled"
        self.status_label.config(text=f"Face tracking: {state}")

    def on_closing(self):
        self.camera.release()
        self.window.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = WebcamProApp(root)
    root.mainloop()
