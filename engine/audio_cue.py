import sys
import threading
from typing import Optional


class AudioCueManager:
    """
    Non-blocking procedural audio cues (shutter click, countdown beeps, recording chimes)
    using native Windows winsound.
    """

    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self._is_windows = sys.platform.startswith("win")
        self._winsound: Optional[object] = None
        if self._is_windows:
            try:
                import winsound
                self._winsound = winsound
            except ImportError:
                pass

    def _play_async(self, func):
        if not self.enabled or not self._winsound:
            return
        threading.Thread(target=func, daemon=True).start()

    def play_shutter_click(self):
        """Simulate realistic mechanical camera shutter click."""
        def _task():
            try:
                self._winsound.Beep(2400, 35)
                self._winsound.Beep(1800, 45)
            except Exception:
                pass
        self._play_async(_task)

    def play_countdown_tick(self):
        """Play low-tone countdown pulse for 3, 2, 1."""
        def _task():
            try:
                self._winsound.Beep(880, 80)
            except Exception:
                pass
        self._play_async(_task)

    def play_countdown_go(self):
        """Play high-tone countdown snap cue."""
        def _task():
            try:
                self._winsound.Beep(1760, 140)
            except Exception:
                pass
        self._play_async(_task)

    def play_record_start(self):
        """Play rising chime when recording begins."""
        def _task():
            try:
                self._winsound.Beep(700, 60)
                self._winsound.Beep(1100, 80)
            except Exception:
                pass
        self._play_async(_task)

    def play_record_stop(self):
        """Play falling chime when recording ends."""
        def _task():
            try:
                self._winsound.Beep(1100, 60)
                self._winsound.Beep(700, 80)
            except Exception:
                pass
        self._play_async(_task)
