import io
import sys
from PIL import Image
import numpy as np


class ClipboardHelper:
    """Helper to copy images or text directly to the system clipboard."""

    @staticmethod
    def copy_text(text: str) -> bool:
        try:
            import pyperclip
            pyperclip.copy(text)
            return True
        except Exception:
            return False

    @staticmethod
    def copy_image(image_input) -> bool:
        """
        Copy a PIL Image, numpy array (OpenCV BGR), or file path to Windows Clipboard.
        """
        if not sys.platform.startswith("win"):
            return False

        try:
            import win32clipboard

            if isinstance(image_input, str):
                pil_img = Image.open(image_input)
            elif isinstance(image_input, np.ndarray):
                # OpenCV BGR -> RGB
                import cv2
                rgb = cv2.cvtColor(image_input, cv2.COLOR_BGR2RGB)
                pil_img = Image.fromarray(rgb)
            elif isinstance(image_input, Image.Image):
                pil_img = image_input
            else:
                return False

            output = io.BytesIO()
            pil_img.convert("RGB").save(output, "BMP")
            data = output.getvalue()[14:]  # Strip BMP 14-byte header to obtain DIB
            output.close()

            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
            win32clipboard.CloseClipboard()
            return True
        except Exception as e:
            print(f"[ClipboardHelper] Failed to copy image: {e}")
            return False
