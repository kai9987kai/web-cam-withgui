"""
camera.py - Backward-compatible Camera module powered by the NextGen Webcam Studio engine.
Fixes previous crashes (Sepia float bug, codec failures, thread deadlocks) while providing
seamless backward compatibility for external callers.
"""

import os
import cv2
import time
from typing import Optional, List, Tuple
import numpy as np

from engine.camera_stream import CameraStream
from engine.filter_engine import FilterEngine
from engine.ai_vision import AIVisionSuite
from engine.recorder import MediaRecorder


class Camera:
    """
    High-performance webcam wrapper supporting legacy API signatures
    while utilizing the new robust multi-threaded engine.
    """

    def __init__(self, camera_index: int = 0):
        self.stream = CameraStream(camera_index=camera_index)
        self.filters = FilterEngine()
        self.ai = AIVisionSuite()
        self.recorder = MediaRecorder()

        self.camera_index = camera_index
        self.width = self.stream.width
        self.height = self.stream.height
        self.running = True

        # Face tracking cascade compatibility
        self.face_cascade = self.ai.face_cascade

    @property
    def frame(self) -> Optional[np.ndarray]:
        ret, frm = self.get_frame()
        return frm if ret else None

    @property
    def ret(self) -> bool:
        ret, _ = self.stream.get_frame()
        return ret

    @property
    def is_recording(self) -> bool:
        return self.recorder.is_recording

    @property
    def show_faces(self) -> bool:
        return self.ai.face_tracking_enabled

    @show_faces.setter
    def show_faces(self, val: bool):
        self.ai.face_tracking_enabled = bool(val)

    @property
    def filter_mode(self) -> str:
        return self.filters.current_filter

    @filter_mode.setter
    def filter_mode(self, val: str):
        self.filters.current_filter = str(val)

    @staticmethod
    def list_cameras(max_search: int = 5) -> List[int]:
        """Enumerate available camera devices."""
        return CameraStream.list_cameras(max_search=max_search)

    def switch_camera(self, new_index: int):
        """Switch active camera capture device."""
        if new_index == self.camera_index:
            return
        success = self.stream.switch_camera(new_index)
        if success or self.stream.is_synthetic:
            self.camera_index = new_index
            self.width = self.stream.width
            self.height = self.stream.height
        else:
            raise ValueError(f"Could not open camera {new_index}")

    def get_frame(self) -> Tuple[bool, Optional[np.ndarray]]:
        """Get the latest processed camera frame."""
        ret, raw_frame = self.stream.get_frame()
        if not ret or raw_frame is None:
            return False, None

        # Process through filter engine & AI
        processed = self.filters.process(raw_frame)
        processed = self.ai.process(processed)

        # Feed to recorder if recording
        if self.recorder.is_recording:
            self.recorder.feed_video_frame(processed)

        return True, processed

    def take_snapshot(self) -> Optional[str]:
        """Capture a photo snapshot and return saved file path."""
        ret, frame = self.get_frame()
        if ret and frame is not None:
            return self.recorder.take_snapshot(frame, file_format="png", prefix="snapshot")
        return None

    def start_recording(self) -> Optional[str]:
        """Start synchronized MP4 video recording."""
        if not self.recorder.is_recording:
            return self.recorder.start_recording(self.width, self.height, fps=self.stream.fps or 30.0)
        return None

    def stop_recording(self):
        """Stop video recording."""
        if self.recorder.is_recording:
            self.recorder.stop_recording()

    def release(self):
        """Release all camera and recording resources."""
        self.running = False
        if self.recorder.is_recording:
            self.recorder.stop_recording()
        self.stream.release()
