import sys
import time
import threading
from typing import Tuple, List, Optional
import cv2
import numpy as np


class CameraStream:
    """
    High-performance multi-threaded camera stream with DirectShow backend support,
    dynamic resolution negotiation, hardware FPS calculation, and synthetic fallback.
    """

    PRESET_RESOLUTIONS = {
        "1080p Full HD": (1920, 1080),
        "720p HD": (1280, 720),
        "480p SD": (640, 480),
        "360p Compact": (640, 360),
    }

    def __init__(self, camera_index: int = 0, target_res: Tuple[int, int] = (1280, 720)):
        self.camera_index = camera_index
        self.target_res = target_res
        self.cap: Optional[cv2.VideoCapture] = None
        self.is_synthetic = False

        self.width = target_res[0]
        self.height = target_res[1]
        self.frame: Optional[np.ndarray] = None
        self.ret = False
        self.running = False
        self.lock = threading.Lock()
        self.thread: Optional[threading.Thread] = None

        # FPS calculation metrics
        self.fps = 0.0
        self._fps_frame_count = 0
        self._fps_start_time = time.time()

        # Connect camera
        self._open_device(camera_index, target_res)
        self.start()

    @staticmethod
    def list_cameras(max_search: int = 4) -> List[int]:
        """
        Enumerate available video capture devices using DirectShow on Windows.
        """
        available = []
        is_windows = sys.platform.startswith("win")
        backend = cv2.CAP_DSHOW if is_windows else cv2.CAP_ANY

        for idx in range(max_search):
            try:
                cap = cv2.VideoCapture(idx, backend)
                if cap.isOpened():
                    # Check if we can read or if device is truly available
                    ret, _ = cap.read()
                    if ret or cap.isOpened():
                        available.append(idx)
                    cap.release()
            except Exception:
                pass

        return available

    def _open_device(self, camera_index: int, target_res: Tuple[int, int]):
        """Open physical camera device with preferred backend or fall back to synthetic camera."""
        is_windows = sys.platform.startswith("win")
        backend = cv2.CAP_DSHOW if is_windows else cv2.CAP_ANY

        if self.cap is not None:
            try:
                self.cap.release()
            except Exception:
                pass
            self.cap = None

        self.is_synthetic = False
        try:
            self.cap = cv2.VideoCapture(camera_index, backend)
            if not self.cap.isOpened() and backend != cv2.CAP_ANY:
                # Fallback to default backend
                self.cap = cv2.VideoCapture(camera_index, cv2.CAP_ANY)

            if not self.cap.isOpened():
                raise RuntimeError(f"Could not open device at index {camera_index}")

            # Request desired resolution
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, target_res[0])
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, target_res[1])

            # Query negotiated properties
            actual_w = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_h = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            if actual_w > 0 and actual_h > 0:
                self.width = actual_w
                self.height = actual_h
            else:
                self.width, self.height = target_res

            # Synchronous initial frame read to ensure frame is immediately ready
            ret, frame = self.cap.read()
            if ret and frame is not None:
                self.frame = frame
                self.ret = True

        except Exception as e:
            # Fallback to synthetic studio test pattern
            print(f"[CameraStream] Hardware capture unavailable ({e}). Activating synthetic stream.")
            self.is_synthetic = True
            self.width, self.height = target_res
            self.frame = self._generate_synthetic_frame(0)
            self.ret = True

    def set_resolution(self, width: int, height: int) -> Tuple[int, int]:
        """Dynamically update stream resolution."""
        self.target_res = (width, height)
        if not self.is_synthetic and self.cap and self.cap.isOpened():
            with self.lock:
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
                self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or width
                self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or height
        else:
            self.width, self.height = width, height
        return self.width, self.height

    def switch_camera(self, new_index: int) -> bool:
        """Switch camera device safely."""
        self.stop()
        self.camera_index = new_index
        self._open_device(new_index, self.target_res)
        self.start()
        return not self.is_synthetic

    def start(self):
        """Start background frame capture loop."""
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._capture_worker, daemon=True)
        self.thread.start()

    def stop(self):
        """Stop background capture loop and wait for thread to terminate."""
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1.5)
            self.thread = None
        if self.cap:
            try:
                self.cap.release()
            except Exception:
                pass
            self.cap = None

    def _generate_synthetic_frame(self, frame_idx: int) -> np.ndarray:
        """Generates a professional SMPTE-style test pattern with moving elements."""
        w, h = self.width, self.height
        frame = np.zeros((h, w, 3), dtype=np.uint8)

        # Standard 7 color bars
        colors = [
            (255, 255, 255),  # White
            (0, 255, 255),    # Yellow
            (255, 255, 0),    # Cyan
            (0, 255, 0),      # Green
            (255, 0, 255),    # Magenta
            (0, 0, 255),      # Red
            (255, 0, 0)       # Blue
        ]
        bar_w = w // len(colors)
        bar_h = int(h * 0.70)
        for i, col in enumerate(colors):
            x1 = i * bar_w
            x2 = w if i == len(colors) - 1 else (i + 1) * bar_w
            frame[0:bar_h, x1:x2] = col

        # Lower section: gradient & dark bands
        frame[bar_h:h, :] = (24, 28, 36)

        # Animated bouncing radar dot to confirm live feed
        speed = 8
        osc = int((time.time() * 120) % (w - 100)) + 50
        cv2.circle(frame, (osc, bar_h + 35), 18, (0, 210, 255), -1)
        cv2.circle(frame, (osc, bar_h + 35), 24, (255, 255, 255), 2)

        # Studio info text overlay
        cv2.putText(frame, "STUDIO TEST PATTERN - CAMERA OFFLINE / VIRTUAL", (30, bar_h + 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (240, 240, 240), 2, cv2.LINE_AA)
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        cv2.putText(frame, f"LIVE TIMECODE: {timestamp} | {w}x{h}", (30, bar_h + 75),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (160, 220, 255), 1, cv2.LINE_AA)

        return frame

    def _capture_worker(self):
        """Background thread constantly updating the latest frame."""
        synthetic_counter = 0
        while self.running:
            if not self.is_synthetic and self.cap and self.cap.isOpened():
                ret, frame = self.cap.read()
                if ret and frame is not None:
                    with self.lock:
                        self.frame = frame
                        self.ret = True
                        self._update_fps()
                else:
                    # Device read failed or disconnected
                    time.sleep(0.02)
            else:
                # Synthetic generator
                frame = self._generate_synthetic_frame(synthetic_counter)
                synthetic_counter += 1
                with self.lock:
                    self.frame = frame
                    self.ret = True
                    self._update_fps()
                time.sleep(0.033)  # ~30 FPS

    def _update_fps(self):
        """Update hardware capture FPS counter."""
        self._fps_frame_count += 1
        elapsed = time.time() - self._fps_start_time
        if elapsed >= 1.0:
            self.fps = self._fps_frame_count / elapsed
            self._fps_frame_count = 0
            self._fps_start_time = time.time()

    def get_frame(self) -> Tuple[bool, Optional[np.ndarray]]:
        """Thread-safe retrieval of latest frame clone."""
        with self.lock:
            if self.ret and self.frame is not None:
                return True, self.frame.copy()
            return False, None

    def release(self):
        """Full cleanup and release of capture device."""
        self.stop()
