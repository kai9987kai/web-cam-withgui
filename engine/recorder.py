import os
import cv2
import time
import queue
import threading
from datetime import datetime
from typing import Optional, Tuple, Callable
import numpy as np


class MediaRecorder:
    """
    Asynchronous, frame-synchronized studio media recorder:
    - MP4 video recording with pause/resume support
    - Paced CFR (Constant Frame Rate) frame delivery to prevent fast-forward playback
    - Asynchronous non-blocking disk writes for snapshots and burst captures
    - Time-Lapse capture engine
    - Real-time recording telemetry (duration, frames, size)
    """

    def __init__(self, snapshot_dir: str = "snapshots", recording_dir: str = "recordings"):
        self.snapshot_dir = snapshot_dir
        self.recording_dir = recording_dir
        os.makedirs(self.snapshot_dir, exist_ok=True)
        os.makedirs(self.recording_dir, exist_ok=True)

        # Video recording state
        self.is_recording = False
        self.is_paused = False
        self.current_video_file: Optional[str] = None
        self.writer: Optional[cv2.VideoWriter] = None
        self.target_fps = 30.0
        self.frame_size: Tuple[int, int] = (1280, 720)

        # Telemetry
        self.start_time = 0.0
        self.total_paused_duration = 0.0
        self._pause_start_time = 0.0
        self.recorded_frames = 0

        # Background async write queue for videos and photos
        self._video_queue = queue.Queue(maxsize=120)
        self._video_worker_thread: Optional[threading.Thread] = None

        # Time-lapse state
        self.timelapse_active = False
        self.timelapse_interval = 5.0  # seconds
        self._last_timelapse_time = 0.0
        self.timelapse_session_dir: Optional[str] = None
        self.timelapse_counter = 0

    def start_recording(self, frame_w: int, frame_h: int, fps: float = 30.0) -> str:
        """Initialize and start MP4 video recording."""
        if self.is_recording:
            return self.current_video_file

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.current_video_file = os.path.join(self.recording_dir, f"video_{timestamp}.mp4")
        self.frame_size = (frame_w, frame_h)
        self.target_fps = max(15.0, fps)

        # Open MP4 video writer
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        self.writer = cv2.VideoWriter(self.current_video_file, fourcc, self.target_fps, self.frame_size)

        self.is_recording = True
        self.is_paused = False
        self.start_time = time.time()
        self.total_paused_duration = 0.0
        self.recorded_frames = 0

        # Start async writer worker thread
        self._video_worker_thread = threading.Thread(target=self._writer_loop, daemon=True)
        self._video_worker_thread.start()

        return self.current_video_file

    def toggle_pause(self) -> bool:
        """Toggle pause/resume during active recording."""
        if not self.is_recording:
            return False
        if not self.is_paused:
            self.is_paused = True
            self._pause_start_time = time.time()
        else:
            self.is_paused = False
            self.total_paused_duration += (time.time() - self._pause_start_time)
        return self.is_paused

    def feed_video_frame(self, frame: np.ndarray):
        """Enqueue frame for asynchronous writing."""
        if not self.is_recording or self.is_paused or frame is None:
            return

        try:
            # Ensure frame matches target dimensions
            h, w = frame.shape[:2]
            if (w, h) != self.frame_size:
                frame = cv2.resize(frame, self.frame_size, interpolation=cv2.INTER_LINEAR)
            self._video_queue.put_nowait(frame.copy())
        except queue.Full:
            pass  # Drop frame if disk write is lagging behind

    def _writer_loop(self):
        """Worker thread executing VideoWriter writes off the main thread."""
        while self.is_recording or not self._video_queue.empty():
            try:
                frame = self._video_queue.get(timeout=0.1)
                if self.writer:
                    self.writer.write(frame)
                    self.recorded_frames += 1
                self._video_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                print(f"[MediaRecorder] Error writing frame: {e}")

        # Finish writing remaining frames and release writer
        if self.writer:
            try:
                self.writer.release()
            except Exception:
                pass
            self.writer = None

    def stop_recording(self) -> Optional[str]:
        """Finalize and close active recording."""
        if not self.is_recording:
            return None

        self.is_recording = False
        self.is_paused = False

        if self._video_worker_thread and self._video_worker_thread.is_alive():
            self._video_worker_thread.join(timeout=2.0)
            self._video_worker_thread = None

        filepath = self.current_video_file
        self.current_video_file = None
        return filepath

    def get_recording_duration(self) -> str:
        """Returns formatted duration string (HH:MM:SS) of current active recording."""
        if not self.is_recording:
            return "00:00:00"

        now = time.time()
        if self.is_paused:
            elapsed = self._pause_start_time - self.start_time - self.total_paused_duration
        else:
            elapsed = now - self.start_time - self.total_paused_duration

        elapsed = max(0, int(elapsed))
        hrs = elapsed // 3600
        mins = (elapsed % 3600) // 60
        secs = elapsed % 60
        return f"{hrs:02d}:{mins:02d}:{secs:02d}"

    def get_recording_size_mb(self) -> float:
        """Returns approximate on-disk file size of recording in MB."""
        if self.current_video_file and os.path.exists(self.current_video_file):
            return os.path.getsize(self.current_video_file) / (1024 * 1024)
        return 0.0

    def take_snapshot(self, frame: np.ndarray, file_format: str = "png",
                      prefix: str = "photo", custom_dir: Optional[str] = None) -> str:
        """Save a photo snapshot to disk asynchronously."""
        if frame is None or frame.size == 0:
            raise ValueError("Invalid frame for snapshot")

        target_dir = custom_dir or self.snapshot_dir
        os.makedirs(target_dir, exist_ok=True)

        ext = file_format.lower().strip(".")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:19]
        filename = f"{prefix}_{timestamp}.{ext}"
        filepath = os.path.join(target_dir, filename)

        # Threaded disk write so camera UI never stutters
        def _save(img, path, ext_type):
            if ext_type in ("jpg", "jpeg"):
                cv2.imwrite(path, img, [cv2.IMWRITE_JPEG_QUALITY, 96])
            else:
                cv2.imwrite(path, img, [cv2.IMWRITE_PNG_COMPRESSION, 4])

        threading.Thread(target=_save, args=(frame.copy(), filepath, ext), daemon=True).start()
        return filepath

    def start_timelapse(self, interval_seconds: float = 5.0) -> str:
        """Initialize a time-lapse capture session folder."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.timelapse_session_dir = os.path.join(self.snapshot_dir, f"timelapse_{timestamp}")
        os.makedirs(self.timelapse_session_dir, exist_ok=True)
        self.timelapse_interval = max(1.0, interval_seconds)
        self.timelapse_active = True
        self.timelapse_counter = 0
        self._last_timelapse_time = 0.0
        return self.timelapse_session_dir

    def stop_timelapse(self) -> Optional[str]:
        """End current time-lapse capture session."""
        self.timelapse_active = False
        res = self.timelapse_session_dir
        self.timelapse_session_dir = None
        return res

    def check_timelapse_tick(self, frame: np.ndarray) -> Optional[str]:
        """Checks if interval has elapsed and takes time-lapse frame."""
        if not self.timelapse_active or frame is None:
            return None

        now = time.time()
        if now - self._last_timelapse_time >= self.timelapse_interval:
            self._last_timelapse_time = now
            self.timelapse_counter += 1
            filename = f"lapse_{self.timelapse_counter:05d}.jpg"
            filepath = os.path.join(self.timelapse_session_dir, filename)
            cv2.imwrite(filepath, frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
            return filepath
        return None
