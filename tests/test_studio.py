import os
import time
import unittest
import numpy as np
import cv2

from engine.camera_stream import CameraStream
from engine.filter_engine import FilterEngine
from engine.ai_vision import AIVisionSuite
from engine.recorder import MediaRecorder
from camera import Camera


class TestWebcamStudioEngine(unittest.TestCase):
    """Comprehensive test suite for Webcam Studio Pro engines and components."""

    def setUp(self):
        # Create synthetic test frame (720p HD)
        self.test_frame = np.zeros((720, 1280, 3), dtype=np.uint8)
        # Add gradient and colored shapes
        self.test_frame[:, :] = (80, 120, 160)
        cv2.circle(self.test_frame, (640, 360), 100, (255, 200, 0), -1)
        cv2.rectangle(self.test_frame, (200, 200), (450, 450), (0, 0, 255), -1)

    def test_filter_engine_all_presets(self):
        """Test that every artistic filter runs cleanly and returns valid frames."""
        engine = FilterEngine()
        for f_name in FilterEngine.AVAILABLE_FILTERS:
            engine.current_filter = f_name
            out = engine.process(self.test_frame)
            self.assertIsNotNone(out, f"Filter {f_name} returned None")
            self.assertEqual(out.shape, self.test_frame.shape, f"Filter {f_name} altered frame shape")
            self.assertEqual(out.dtype, np.uint8, f"Filter {f_name} dtype is not uint8")

    def test_filter_engine_adjustments(self):
        """Test color adjustments (brightness, contrast, saturation, warmth, zoom)."""
        engine = FilterEngine()
        engine.brightness = 25.0
        engine.contrast = 1.4
        engine.saturation = 1.3
        engine.warmth = 15.0
        engine.sharpness = 2.0
        engine.zoom_level = 1.5
        engine.pan_x = 0.2
        engine.pan_y = -0.1

        out = engine.process(self.test_frame)
        self.assertIsNotNone(out)
        self.assertEqual(out.shape, self.test_frame.shape)

        # Test reset
        engine.reset_adjustments()
        self.assertEqual(engine.brightness, 0.0)
        self.assertEqual(engine.contrast, 1.0)
        self.assertEqual(engine.zoom_level, 1.0)

    def test_filter_engine_transforms(self):
        """Test mirroring, flipping, and rotation."""
        engine = FilterEngine()
        engine.flip_h = True
        engine.flip_v = True
        out = engine.process(self.test_frame)
        self.assertIsNotNone(out)

    def test_ai_vision_suite(self):
        """Test AI vision features (face detection, AR overlays, QR, motion)."""
        ai = AIVisionSuite()

        # Enable features
        ai.face_tracking_enabled = True
        ai.ar_prop = "Sunglasses"
        ai.privacy_mode = "Blur"
        ai.motion_enabled = True

        out = ai.process(self.test_frame)
        self.assertIsNotNone(out)
        self.assertEqual(out.shape, self.test_frame.shape)

        # Test AR Crown & Mustache
        ai.ar_prop = "Crown"
        out_crown = ai.process(self.test_frame)
        self.assertIsNotNone(out_crown)

        ai.ar_prop = "Mustache"
        out_mustache = ai.process(self.test_frame)
        self.assertIsNotNone(out_mustache)

    def test_media_recorder_snapshot(self):
        """Test saving PNG and JPG snapshots."""
        recorder = MediaRecorder(snapshot_dir="test_snapshots", recording_dir="test_recordings")
        png_path = recorder.take_snapshot(self.test_frame, file_format="png")
        jpg_path = recorder.take_snapshot(self.test_frame, file_format="jpg")

        time.sleep(0.3)  # Allow async write to complete
        self.assertTrue(os.path.exists(png_path), f"PNG file not created: {png_path}")
        self.assertTrue(os.path.exists(jpg_path), f"JPG file not created: {jpg_path}")

        # Cleanup
        try:
            if os.path.exists(png_path):
                os.remove(png_path)
            if os.path.exists(jpg_path):
                os.remove(jpg_path)
            if os.path.exists("test_snapshots"):
                os.rmdir("test_snapshots")
        except Exception:
            pass

    def test_media_recorder_video_mp4(self):
        """Test recording MP4 video with feed_video_frame, pause, and stop."""
        recorder = MediaRecorder(snapshot_dir="test_snapshots", recording_dir="test_recordings")
        vid_path = recorder.start_recording(1280, 720, fps=30.0)
        self.assertTrue(recorder.is_recording)

        for _ in range(15):
            recorder.feed_video_frame(self.test_frame)
            time.sleep(0.01)

        recorder.toggle_pause()
        self.assertTrue(recorder.is_paused)
        recorder.toggle_pause()
        self.assertFalse(recorder.is_paused)

        stopped_path = recorder.stop_recording()
        self.assertEqual(stopped_path, vid_path)
        self.assertFalse(recorder.is_recording)

        time.sleep(0.5)
        self.assertTrue(os.path.exists(vid_path), f"MP4 file not created: {vid_path}")
        self.assertGreater(os.path.getsize(vid_path), 0, "MP4 file is empty")

        # Cleanup
        try:
            if os.path.exists(vid_path):
                os.remove(vid_path)
            if os.path.exists("test_recordings"):
                os.rmdir("test_recordings")
        except Exception:
            pass

    def test_camera_stream_synthetic(self):
        """Test CameraStream synthetic fallback mode."""
        stream = CameraStream(camera_index=999, target_res=(640, 480))
        self.assertTrue(stream.is_synthetic)
        self.assertTrue(stream.running)

        time.sleep(0.1)
        ret, frame = stream.get_frame()
        self.assertTrue(ret)
        self.assertIsNotNone(frame)
        self.assertEqual(frame.shape, (480, 640, 3))

        stream.release()
        self.assertFalse(stream.running)

    def test_legacy_camera_compatibility(self):
        """Test backward compatibility of camera.py Camera class."""
        cam = Camera(camera_index=0)
        self.assertIsNotNone(cam)
        ret, frame = cam.get_frame()
        self.assertTrue(ret)
        self.assertIsNotNone(frame)

        # Test Sepia (which previously crashed)
        cam.filter_mode = "Sepia"
        ret_sepia, frame_sepia = cam.get_frame()
        self.assertTrue(ret_sepia)
        self.assertIsNotNone(frame_sepia)

        # Test snapshot
        snap = cam.take_snapshot()
        time.sleep(0.2)
        if snap and os.path.exists(snap):
            os.remove(snap)

        cam.release()


if __name__ == "__main__":
    unittest.main()
