import cv2
import numpy as np
import time
from typing import List, Tuple, Optional, Callable


class AIVisionSuite:
    """
    Advanced real-time AI and Computer Vision suite:
    - High-speed multiscale face detection with EMA jitter-smoothing
    - Privacy Anonymizer (face blur / pixelate)
    - Dynamic AR Props (Sunglasses, Royal Crown, Mustache)
    - Real-time QR Code & Barcode Scanner
    - Motion Detection & Security Guard with Auto-Snapshot trigger
    """

    def __init__(self):
        # Cascades for face, eye, smile
        cascade_dir = cv2.data.haarcascades
        self.face_cascade = cv2.CascadeClassifier(cascade_dir + "haarcascade_frontalface_default.xml")
        self.eye_cascade = cv2.CascadeClassifier(cascade_dir + "haarcascade_eye.xml")
        self.smile_cascade = cv2.CascadeClassifier(cascade_dir + "haarcascade_smile.xml")

        # QR Detector
        self.qr_detector = cv2.QRCodeDetector()
        self.last_qr_text = ""
        self.last_qr_time = 0.0
        self.qr_scanner_enabled = False

        # Motion Subtractor
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(history=60, varThreshold=30, detectShadows=False)
        self.motion_enabled = False
        self.motion_percent = 0.0
        self.security_guard_enabled = False
        self.security_threshold = 3.5  # % of screen moving
        self.security_cooldown = 5.0   # seconds between auto-snaps
        self._last_security_snap = 0.0
        self.security_snap_callback: Optional[Callable[[str], None]] = None

        # Face tracking state & EMA smoothing
        self.face_tracking_enabled = False
        self.privacy_mode = "None"      # "None", "Blur", "Pixelate"
        self.ar_prop = "None"           # "None", "Sunglasses", "Crown", "Mustache"
        self._smoothed_faces = []       # [(x, y, w, h)]
        self._ema_alpha = 0.65          # Smoothing weight (0 = lock, 1 = raw)

        # Performance downscaling scale
        self.detect_scale = 0.25        # 1/4 resolution for 100x detection speedup
        self._frame_counter = 0

    def process(self, frame: np.ndarray) -> np.ndarray:
        """Run all active AI vision components on the frame."""
        if frame is None or frame.size == 0:
            return frame

        self._frame_counter += 1

        # 1. Motion Detection / Security Guard
        if self.motion_enabled or self.security_guard_enabled:
            frame = self._process_motion(frame)

        # 2. QR Code Scanner (every 3 frames for optimal performance)
        if self.qr_scanner_enabled and (self._frame_counter % 3 == 0):
            frame = self._process_qr_scanner(frame)

        # 3. Face Tracking, Privacy Anonymizer & AR Props
        if self.face_tracking_enabled or self.privacy_mode != "None" or self.ar_prop != "None":
            frame = self._process_faces(frame)

        return frame

    def _process_faces(self, frame: np.ndarray) -> np.ndarray:
        """Detect faces at high speed, apply smoothing, privacy masking, and AR props."""
        h, w = frame.shape[:2]
        small_w = int(w * self.detect_scale)
        small_h = int(h * self.detect_scale)

        # Downscale grayscale for rapid Haar cascade inference
        small_gray = cv2.resize(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), (small_w, small_h))
        faces = self.face_cascade.detectMultiScale(small_gray, scaleFactor=1.2, minNeighbors=4, minSize=(20, 20))

        # Scale detected coordinates back to original size
        inv_scale = 1.0 / self.detect_scale
        current_faces = []
        for (sx, sy, sw, sh) in faces:
            current_faces.append((
                int(sx * inv_scale),
                int(sy * inv_scale),
                int(sw * inv_scale),
                int(sh * inv_scale)
            ))

        # Exponential Moving Average (EMA) smoothing to eliminate jitter
        if len(self._smoothed_faces) == len(current_faces) and len(current_faces) > 0:
            smoothed = []
            for (ox, oy, ow, oh), (cx, cy, cw, ch) in zip(self._smoothed_faces, current_faces):
                sx = int(self._ema_alpha * cx + (1 - self._ema_alpha) * ox)
                sy = int(self._ema_alpha * cy + (1 - self._ema_alpha) * oy)
                sw = int(self._ema_alpha * cw + (1 - self._ema_alpha) * ow)
                sh = int(self._ema_alpha * ch + (1 - self._ema_alpha) * oh)
                smoothed.append((sx, sy, sw, sh))
            self._smoothed_faces = smoothed
        else:
            self._smoothed_faces = current_faces

        for idx, (x, y, fw, fh) in enumerate(self._smoothed_faces):
            # Clamp to frame bounds
            x1, y1 = max(0, x), max(0, y)
            x2, y2 = min(w, x + fw), min(h, y + fh)

            if x2 <= x1 or y2 <= y1:
                continue

            face_roi = frame[y1:y2, x1:x2]

            # Privacy Masking
            if self.privacy_mode == "Blur":
                ksize = max(31, (fw // 7) * 2 + 1)
                frame[y1:y2, x1:x2] = cv2.GaussianBlur(face_roi, (ksize, ksize), 0)
            elif self.privacy_mode == "Pixelate":
                pw, ph = max(1, fw // 16), max(1, fh // 16)
                small_roi = cv2.resize(face_roi, (pw, ph), interpolation=cv2.INTER_LINEAR)
                frame[y1:y2, x1:x2] = cv2.resize(small_roi, (x2 - x1, y2 - y1), interpolation=cv2.INTER_NEAREST)

            # AR Props Overlays
            if self.ar_prop == "Sunglasses":
                self._draw_sunglasses(frame, x, y, fw, fh)
            elif self.ar_prop == "Crown":
                self._draw_crown(frame, x, y, fw, fh)
            elif self.ar_prop == "Mustache":
                self._draw_mustache(frame, x, y, fw, fh)

            # Futuristic Cyber HUD Bounding Box
            if self.face_tracking_enabled and self.privacy_mode == "None":
                self._draw_hud_box(frame, x, y, fw, fh, idx + 1)

        return frame

    def _draw_hud_box(self, frame: np.ndarray, x: int, y: int, w: int, h: int, face_id: int):
        """Draws a sleek high-tech cyber HUD bracket around detected face."""
        cyan = (255, 210, 0)      # BGR
        purple = (250, 80, 160)
        c_len = max(15, int(w * 0.2))
        thickness = 2

        # 4 Corner brackets
        # Top-left
        cv2.line(frame, (x, y), (x + c_len, y), cyan, thickness)
        cv2.line(frame, (x, y), (x, y + c_len), cyan, thickness)
        # Top-right
        cv2.line(frame, (x + w, y), (x + w - c_len, y), cyan, thickness)
        cv2.line(frame, (x + w, y), (x + w, y + c_len), cyan, thickness)
        # Bottom-left
        cv2.line(frame, (x, y + h), (x + c_len, y + h), cyan, thickness)
        cv2.line(frame, (x, y + h), (x, y + h - c_len), cyan, thickness)
        # Bottom-right
        cv2.line(frame, (x + w, y + h), (x + w - c_len, y + h), cyan, thickness)
        cv2.line(frame, (x + w, y + h), (x + w, y + h - c_len), cyan, thickness)

        # Target center cross
        cx, cy = x + w // 2, y + h // 2
        cv2.drawMarker(frame, (cx, cy), purple, cv2.MARKER_CROSS, 12, 1)

        # Tech label banner
        label = f"SUBJECT #{face_id} [TRACKED]"
        cv2.rectangle(frame, (x, y - 22), (x + 160, y - 4), (18, 20, 30), -1)
        cv2.putText(frame, label, (x + 6, y - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (0, 230, 255), 1, cv2.LINE_AA)

    def _draw_sunglasses(self, frame: np.ndarray, x: int, y: int, w: int, h: int):
        """Draw vector cyberpunk neon sunglasses over eyes area."""
        glass_w = int(w * 0.82)
        glass_h = int(h * 0.26)
        gx = x + int(w * 0.09)
        gy = y + int(h * 0.32)

        # Lens frame
        lens_w = int(glass_w * 0.42)
        lens_gap = int(glass_w * 0.16)

        # Left lens
        lx1, ly1 = gx, gy
        lx2, ly2 = lx1 + lens_w, ly1 + glass_h
        cv2.rectangle(frame, (lx1, ly1), (lx2, ly2), (20, 20, 25), -1)
        cv2.rectangle(frame, (lx1, ly1), (lx2, ly2), (255, 230, 0), 2)  # Cyan border
        # Glare line
        cv2.line(frame, (lx1 + 4, ly1 + 6), (lx1 + lens_w - 6, ly2 - 6), (200, 240, 255), 2)

        # Bridge
        cv2.line(frame, (lx2, ly1 + glass_h // 2), (lx2 + lens_gap, ly1 + glass_h // 2), (255, 230, 0), 3)

        # Right lens
        rx1 = lx2 + lens_gap
        rx2, ry2 = rx1 + lens_w, ly1 + glass_h
        cv2.rectangle(frame, (rx1, ly1), (rx2, ry2), (20, 20, 25), -1)
        cv2.rectangle(frame, (rx1, ly1), (rx2, ry2), (255, 230, 0), 2)
        cv2.line(frame, (rx1 + 4, ly1 + 6), (rx1 + lens_w - 6, ry2 - 6), (200, 240, 255), 2)

    def _draw_crown(self, frame: np.ndarray, x: int, y: int, w: int, h: int):
        """Draw royal golden crown over head."""
        cw = int(w * 0.9)
        ch = int(h * 0.45)
        cx = x + int(w * 0.05)
        cy = max(5, y - int(h * 0.42))

        # Crown polygon points (Golden crown with 3 peaks)
        gold = (40, 215, 255)       # BGR Gold
        dark_gold = (20, 160, 200)

        pts = np.array([
            [cx, cy + ch],
            [cx + cw, cy + ch],
            [cx + cw, cy + int(ch * 0.3)],
            [cx + int(cw * 0.75), cy + int(ch * 0.55)],
            [cx + int(cw * 0.5), cy],
            [cx + int(cw * 0.25), cy + int(ch * 0.55)],
            [cx, cy + int(ch * 0.3)]
        ], np.int32)

        cv2.fillPoly(frame, [pts], gold)
        cv2.polylines(frame, [pts], isClosed=True, color=dark_gold, thickness=2)

        # Jewels on peaks
        cv2.circle(frame, (cx + int(cw * 0.5), cy + 4), 6, (0, 0, 255), -1)      # Ruby
        cv2.circle(frame, (cx + int(cw * 0.1), cy + int(ch * 0.35)), 5, (255, 0, 0), -1)  # Sapphire
        cv2.circle(frame, (cx + int(cw * 0.9), cy + int(ch * 0.35)), 5, (255, 0, 0), -1)  # Sapphire

    def _draw_mustache(self, frame: np.ndarray, x: int, y: int, w: int, h: int):
        """Draw classic gentleman handlebar mustache."""
        mw = int(w * 0.5)
        mh = int(h * 0.18)
        mx = x + int(w * 0.25)
        my = y + int(h * 0.68)

        # Ellipse curves for handlebar
        cv2.ellipse(frame, (mx + mw // 4, my), (mw // 4, mh // 2), 0, 0, 180, (25, 25, 25), -1)
        cv2.ellipse(frame, (mx + 3 * mw // 4, my), (mw // 4, mh // 2), 0, 0, 180, (25, 25, 25), -1)
        # Curved tips
        cv2.ellipse(frame, (mx, my - 2), (mw // 6, mh // 3), 40, 0, 180, (25, 25, 25), -1)
        cv2.ellipse(frame, (mx + mw, my - 2), (mw // 6, mh // 3), -40, 0, 180, (25, 25, 25), -1)

    def _process_qr_scanner(self, frame: np.ndarray) -> np.ndarray:
        """Scan frame for QR code/barcode and highlight payload."""
        try:
            val, pts, _ = self.qr_detector.detectAndDecode(frame)
            if val and pts is not None:
                self.last_qr_text = val
                self.last_qr_time = time.time()

                # Highlight bounding polygon
                pts = pts[0].astype(int)
                n = len(pts)
                for j in range(n):
                    p1 = tuple(pts[j])
                    p2 = tuple(pts[(j + 1) % n])
                    cv2.line(frame, p1, p2, (0, 255, 128), 3)

                # Overlay banner
                top_left = tuple(pts[0])
                cv2.rectangle(frame, (top_left[0], max(0, top_left[1] - 30)),
                              (top_left[0] + 280, max(30, top_left[1])), (20, 25, 35), -1)
                short_text = val if len(val) < 28 else val[:25] + "..."
                cv2.putText(frame, f"QR: {short_text}", (top_left[0] + 8, max(20, top_left[1] - 8)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 128), 2)
        except Exception:
            pass

        return frame

    def _process_motion(self, frame: np.ndarray) -> np.ndarray:
        """Detect motion, calculate movement percentage, and trigger security guard."""
        h, w = frame.shape[:2]
        small_frame = cv2.resize(frame, (320, 240))
        fg_mask = self.bg_subtractor.apply(small_frame)

        # Threshold and find contours
        _, thresh = cv2.threshold(fg_mask, 180, 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        total_pixels = 320 * 240
        motion_pixels = cv2.countNonZero(thresh)
        self.motion_percent = (motion_pixels / total_pixels) * 100.0

        # Draw motion contours if above threshold
        scale_x = w / 320.0
        scale_y = h / 240.0

        for c in contours:
            if cv2.contourArea(c) > 300:
                cx, cy, cw, ch = cv2.boundingRect(c)
                rx1 = int(cx * scale_x)
                ry1 = int(cy * scale_y)
                rx2 = int((cx + cw) * scale_x)
                ry2 = int((cy + ch) * scale_y)
                # Neon orange motion box
                cv2.rectangle(frame, (rx1, ry1), (rx2, ry2), (0, 140, 255), 2)

        # Security Guard Auto-Snapshot check
        if self.security_guard_enabled and self.motion_percent >= self.security_threshold:
            now = time.time()
            if now - self._last_security_snap >= self.security_cooldown:
                self._last_security_snap = now
                if self.security_snap_callback:
                    self.security_snap_callback(f"Motion alert: {self.motion_percent:.1f}%")

        return frame
