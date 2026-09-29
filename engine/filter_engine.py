import cv2
import numpy as np
from typing import Tuple, Dict, Any


class FilterEngine:
    """
    Advanced studio image filter and color grading pipeline with SIMD-accelerated
    OpenCV operations, real-time adjustments, and digital zoom/pan.
    """

    AVAILABLE_FILTERS = [
        "Normal",
        "Grayscale",
        "Noir",
        "Sepia",
        "Cyberpunk",
        "Matrix",
        "Sunset Amber",
        "Ocean Teal",
        "Thermal",
        "Night Vision",
        "Cartoon",
        "Pencil Sketch",
        "Edges",
        "Blur",
        "Pixelate",
        "Invert",
        "Beauty"
    ]

    # Authentic BGR Sepia Matrix
    SEPIA_KERNEL = np.array([
        [0.131, 0.534, 0.272],
        [0.168, 0.686, 0.349],
        [0.189, 0.769, 0.393]
    ], dtype=np.float32)

    def __init__(self):
        self.current_filter = "Normal"

        # Studio Adjustments
        self.brightness: float = 0.0     # -100 to +100
        self.contrast: float = 1.0       # 0.5 to 2.5
        self.saturation: float = 1.0     # 0.0 to 2.5
        self.sharpness: float = 0.0      # 0.0 to 10.0
        self.warmth: float = 0.0         # -50 to +50

        # Transforms
        self.flip_h: bool = False
        self.flip_v: bool = False
        self.rotation_degrees: int = 0   # 0, 90, 180, 270
        self.zoom_level: float = 1.0     # 1.0 to 4.0
        self.pan_x: float = 0.0          # -1.0 to 1.0
        self.pan_y: float = 0.0          # -1.0 to 1.0

    def reset_adjustments(self):
        """Reset all grading sliders to neutral defaults."""
        self.brightness = 0.0
        self.contrast = 1.0
        self.saturation = 1.0
        self.sharpness = 0.0
        self.warmth = 0.0
        self.zoom_level = 1.0
        self.pan_x = 0.0
        self.pan_y = 0.0

    def process(self, frame: np.ndarray) -> np.ndarray:
        """Execute full filtering, transformation, and grading pipeline."""
        if frame is None or frame.size == 0:
            return frame

        # 1. Geometric transforms (Flip, Rotate, Zoom)
        frame = self._apply_transforms(frame)

        # 2. Base Artistic Filter
        frame = self._apply_filter(frame)

        # 3. Color Grading & Adjustments (Brightness, Contrast, Saturation, Warmth, Sharpness)
        frame = self._apply_adjustments(frame)

        return frame

    def _apply_transforms(self, frame: np.ndarray) -> np.ndarray:
        """Applies mirroring, rotation, and digital zoom/pan."""
        h, w = frame.shape[:2]

        # Horizontal & Vertical Flip
        if self.flip_h and self.flip_v:
            frame = cv2.flip(frame, -1)
        elif self.flip_h:
            frame = cv2.flip(frame, 1)
        elif self.flip_v:
            frame = cv2.flip(frame, 0)

        # Rotation
        if self.rotation_degrees == 90:
            frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
        elif self.rotation_degrees == 180:
            frame = cv2.rotate(frame, cv2.ROTATE_180)
        elif self.rotation_degrees == 270:
            frame = cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)

        # Digital Zoom & Pan
        if self.zoom_level > 1.01:
            zh, zw = frame.shape[:2]
            crop_w = int(zw / self.zoom_level)
            crop_h = int(zh / self.zoom_level)

            # Center with pan offset
            center_x = int(zw / 2 + self.pan_x * (zw - crop_w) / 2)
            center_y = int(zh / 2 + self.pan_y * (zh - crop_h) / 2)

            x1 = max(0, min(zw - crop_w, center_x - crop_w // 2))
            y1 = max(0, min(zh - crop_h, center_y - crop_h // 2))
            x2 = x1 + crop_w
            y2 = y1 + crop_h

            cropped = frame[y1:y2, x1:x2]
            frame = cv2.resize(cropped, (zw, zh), interpolation=cv2.INTER_LINEAR)

        return frame

    def _apply_filter(self, frame: np.ndarray) -> np.ndarray:
        """Apply active artistic filter effect."""
        mode = self.current_filter

        if mode == "Normal":
            return frame

        elif mode == "Grayscale":
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            return cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)

        elif mode == "Noir":
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            # High-contrast sigmoid S-curve
            table = np.array([((i / 255.0) ** 1.8) * 255 for i in np.arange(0, 256)]).astype("uint8")
            contrast_gray = cv2.LUT(gray, table)
            return cv2.cvtColor(contrast_gray, cv2.COLOR_GRAY2BGR)

        elif mode == "Sepia":
            sepia = cv2.transform(frame, self.SEPIA_KERNEL)
            return np.clip(sepia, 0, 255).astype(np.uint8)

        elif mode == "Cyberpunk":
            # Vivid neon magenta and cyan highlights
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV).astype(np.float32)
            hsv[..., 1] = np.clip(hsv[..., 1] * 1.5, 0, 255)
            enhanced = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)
            b, g, r = cv2.split(enhanced)
            # Amplify blue/cyan and red/magenta
            b = cv2.addWeighted(b, 1.25, g, 0.1, 10)
            r = cv2.addWeighted(r, 1.35, b, 0.05, 15)
            return cv2.merge([b, g, r])

        elif mode == "Matrix":
            # Phosphor green tint with edge sharpening
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            green = np.zeros_like(frame)
            green[..., 1] = gray  # Put grayscale into green channel
            green[..., 0] = (gray * 0.15).astype(np.uint8)
            green[..., 2] = (gray * 0.1).astype(np.uint8)
            return green

        elif mode == "Sunset Amber":
            b, g, r = cv2.split(frame)
            r = np.clip(r.astype(np.int16) + 35, 0, 255).astype(np.uint8)
            g = np.clip(g.astype(np.int16) + 15, 0, 255).astype(np.uint8)
            b = np.clip(b.astype(np.int16) - 25, 0, 255).astype(np.uint8)
            return cv2.merge([b, g, r])

        elif mode == "Ocean Teal":
            b, g, r = cv2.split(frame)
            b = np.clip(b.astype(np.int16) + 30, 0, 255).astype(np.uint8)
            g = np.clip(g.astype(np.int16) + 20, 0, 255).astype(np.uint8)
            r = np.clip(r.astype(np.int16) - 20, 0, 255).astype(np.uint8)
            return cv2.merge([b, g, r])

        elif mode == "Thermal":
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            return cv2.applyColorMap(gray, cv2.COLORMAP_JET)

        elif mode == "Night Vision":
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            # Add synthetic phosphor green glow + scanlines
            nv = np.zeros_like(frame)
            nv[..., 1] = np.clip(cv2.equalizeHist(gray).astype(np.int16) + 30, 0, 255).astype(np.uint8)
            # Scanlines every 4 pixels
            nv[::4, :, 1] = (nv[::4, :, 1] * 0.6).astype(np.uint8)
            return nv

        elif mode == "Cartoon":
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.medianBlur(gray, 5)
            edges = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 9, 9)
            color = cv2.bilateralFilter(frame, 9, 250, 250)
            return cv2.bitwise_and(color, color, mask=edges)

        elif mode == "Pencil Sketch":
            try:
                dst_gray, dst_color = cv2.pencilSketch(frame, sigma_s=50, sigma_r=0.07, shade_factor=0.04)
                return dst_color
            except Exception:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                inv = 255 - gray
                blur = cv2.GaussianBlur(inv, (21, 21), 0)
                sketch = cv2.divide(gray, 255 - blur, scale=256)
                return cv2.cvtColor(sketch, cv2.COLOR_GRAY2BGR)

        elif mode == "Edges":
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 80, 160)
            # Make edges neon cyan
            neon = np.zeros_like(frame)
            neon[edges > 0] = [255, 230, 0]  # Cyan in BGR
            return neon

        elif mode == "Blur":
            return cv2.GaussianBlur(frame, (25, 25), 0)

        elif mode == "Pixelate":
            h, w = frame.shape[:2]
            scale = 0.05
            small = cv2.resize(frame, (0, 0), fx=scale, fy=scale, interpolation=cv2.INTER_LINEAR)
            return cv2.resize(small, (w, h), interpolation=cv2.INTER_NEAREST)

        elif mode == "Invert":
            return cv2.bitwise_not(frame)

        elif mode == "Beauty":
            # Soft skin smoothing: bilateral filter with subtle blend to retain crisp details
            smooth = cv2.bilateralFilter(frame, d=7, sigmaColor=75, sigmaSpace=75)
            # High-pass blend for sharpening eyes/contour
            return cv2.addWeighted(smooth, 0.75, frame, 0.25, 0)

        return frame

    def _apply_adjustments(self, frame: np.ndarray) -> np.ndarray:
        """Apply Brightness, Contrast, Saturation, Warmth, and Sharpness."""
        is_modified = (self.brightness != 0 or self.contrast != 1.0 or
                       self.saturation != 1.0 or self.warmth != 0 or self.sharpness > 0)
        if not is_modified:
            return frame

        # Contrast & Brightness: output = contrast * frame + brightness
        if self.contrast != 1.0 or self.brightness != 0:
            frame = cv2.convertScaleAbs(frame, alpha=self.contrast, beta=self.brightness)

        # Color Warmth (White Balance shift)
        if self.warmth != 0:
            b, g, r = cv2.split(frame)
            if self.warmth > 0:
                # Warmer: boost Red, decrease Blue
                r = np.clip(r.astype(np.int16) + int(self.warmth), 0, 255).astype(np.uint8)
                b = np.clip(b.astype(np.int16) - int(self.warmth * 0.7), 0, 255).astype(np.uint8)
            else:
                # Cooler: boost Blue, decrease Red
                val = abs(self.warmth)
                b = np.clip(b.astype(np.int16) + int(val), 0, 255).astype(np.uint8)
                r = np.clip(r.astype(np.int16) - int(val * 0.7), 0, 255).astype(np.uint8)
            frame = cv2.merge([b, g, r])

        # Saturation adjustment in HSV
        if self.saturation != 1.0:
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV).astype(np.float32)
            hsv[..., 1] = np.clip(hsv[..., 1] * self.saturation, 0, 255)
            frame = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)

        # Sharpness / Unsharp Mask
        if self.sharpness > 0:
            blur = cv2.GaussianBlur(frame, (0, 0), 3)
            weight = self.sharpness * 0.3
            frame = cv2.addWeighted(frame, 1.0 + weight, blur, -weight, 0)

        return frame
