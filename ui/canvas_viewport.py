import time
import tkinter as tk
from tkinter import ttk
from typing import Optional, Callable
import cv2
import numpy as np
from PIL import Image, ImageTk


class CanvasViewport(tk.Frame):
    """
    Studio-grade high-performance video canvas:
    - C++ SIMD hardware-accelerated aspect-ratio scaling
    - Zero-flicker single image ID reuse
    - Framing composition grids (Rule of Thirds, Center Crosshair, Golden Ratio)
    - Animated shutter flash effect
    - Big glowing countdown timer overlay
    - Interactive pan on drag when digitally zoomed
    - Studio telemetry HUD
    """

    def __init__(self, parent, on_pan_callback: Optional[Callable[[float, float], None]] = None, **kwargs):
        super().__init__(parent, bg="#0C0D14", **kwargs)
        self.on_pan_callback = on_pan_callback

        self.canvas = tk.Canvas(self, bg="#000000", highlightthickness=0, bd=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self._image_id: Optional[int] = None
        self._photo_ref: Optional[ImageTk.PhotoImage] = None

        # Display FPS metrics
        self.display_fps = 0.0
        self._disp_frame_count = 0
        self._disp_start_time = time.time()

        # Composition Grid
        self.grid_mode = "None"  # "None", "Rule of Thirds", "Center Crosshair", "Golden Ratio"

        # Shutter Flash animation
        self._flash_active = False
        self._flash_end_time = 0.0

        # Countdown overlay
        self.countdown_val: Optional[int] = None

        # Watermark & HUD options
        self.show_watermark = False
        self.show_telemetry = True

        # Mouse Drag for Digital Pan
        self._drag_start_x = 0
        self._drag_start_y = 0
        self.canvas.bind("<ButtonPress-1>", self._on_mouse_down)
        self.canvas.bind("<B1-Motion>", self._on_mouse_drag)

    def trigger_flash(self, duration_sec: float = 0.12):
        """Trigger camera flash visual animation."""
        self._flash_active = True
        self._flash_end_time = time.time() + duration_sec

    def set_countdown(self, count: Optional[int]):
        """Set current countdown second or None to disable."""
        self.countdown_val = count

    def cycle_grid_mode(self) -> str:
        """Cycle through framing grid modes."""
        modes = ["None", "Rule of Thirds", "Center Crosshair", "Golden Ratio"]
        idx = (modes.index(self.grid_mode) + 1) % len(modes)
        self.grid_mode = modes[idx]
        return self.grid_mode

    def _on_mouse_down(self, event):
        self._drag_start_x = event.x
        self._drag_start_y = event.y

    def _on_mouse_drag(self, event):
        if self.on_pan_callback:
            dx = (event.x - self._drag_start_x) / 300.0
            dy = (event.y - self._drag_start_y) / 300.0
            self.on_pan_callback(-dx, -dy)
            self._drag_start_x = event.x
            self._drag_start_y = event.y

    def render_frame(self, frame: np.ndarray, capture_fps: float = 0.0,
                     is_recording: bool = False, is_paused: bool = False,
                     recording_duration: str = "00:00:00", active_filter: str = "Normal",
                     motion_percent: float = 0.0, is_security_active: bool = False):
        """Render frame to canvas with all studio overlays."""
        if frame is None or frame.size == 0:
            return

        cw = self.canvas.winfo_width()
        ch = self.canvas.winfo_height()
        if cw < 10 or ch < 10:
            return

        # Frame dimensions
        fh, fw = frame.shape[:2]

        # 1. Shutter Flash Effect
        if self._flash_active:
            if time.time() < self._flash_end_time:
                frame = cv2.addWeighted(frame, 0.25, np.full_like(frame, 255), 0.75, 0)
            else:
                self._flash_active = False

        # 2. Watermark
        if self.show_watermark:
            time_str = time.strftime("%Y-%m-%d  %H:%M:%S")
            cv2.putText(frame, time_str, (20, fh - 20), cv2.FONT_HERSHEY_SIMPLEX,
                        0.65, (0, 0, 0), 3, cv2.LINE_AA)
            cv2.putText(frame, time_str, (20, fh - 20), cv2.FONT_HERSHEY_SIMPLEX,
                        0.65, (255, 255, 255), 1, cv2.LINE_AA)

        # 3. High-performance C++ Aspect-Ratio Scaling
        scale = min(cw / fw, ch / fh)
        nw = max(1, int(fw * scale))
        nh = max(1, int(fh * scale))

        scaled_bgr = cv2.resize(frame, (nw, nh), interpolation=cv2.INTER_LINEAR)
        rgb_frame = cv2.cvtColor(scaled_bgr, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(rgb_frame)
        self._photo_ref = ImageTk.PhotoImage(image=pil_img)

        # Centering coordinates
        pos_x = cw // 2
        pos_y = ch // 2
        rx1 = pos_x - nw // 2
        ry1 = pos_y - nh // 2
        rx2 = rx1 + nw
        ry2 = ry1 + nh

        # Draw / Update video image
        if self._image_id is None:
            self._image_id = self.canvas.create_image(pos_x, pos_y, anchor=tk.CENTER, image=self._photo_ref)
        else:
            self.canvas.coords(self._image_id, pos_x, pos_y)
            self.canvas.itemconfig(self._image_id, image=self._photo_ref)

        # 4. Canvas Overlays (Grid, HUD, Countdown)
        self.canvas.delete("overlay")

        # Composition Guides
        self._draw_grid_overlays(rx1, ry1, nw, nh)

        # Telemetry HUD
        if self.show_telemetry:
            self._draw_telemetry_hud(rx1, ry1, rx2, ry2, fw, fh, capture_fps,
                                    is_recording, is_paused, recording_duration,
                                    active_filter, motion_percent, is_security_active)

        # Countdown Timer Animation
        if self.countdown_val is not None and self.countdown_val > 0:
            self._draw_countdown_overlay(pos_x, pos_y)

        # Update Display FPS
        self._disp_frame_count += 1
        elapsed = time.time() - self._disp_start_time
        if elapsed >= 1.0:
            self.display_fps = self._disp_frame_count / elapsed
            self._disp_frame_count = 0
            self._disp_start_time = time.time()

    def _draw_grid_overlays(self, x: int, y: int, w: int, h: int):
        """Draw composition guide lines on canvas."""
        if self.grid_mode == "None":
            return

        guide_color = "#4ADE80" if self.grid_mode == "Golden Ratio" else "#38BDF8"

        if self.grid_mode == "Rule of Thirds":
            # 2 vertical and 2 horizontal lines
            for i in (1, 2):
                gx = x + (w * i) // 3
                gy = y + (h * i) // 3
                self.canvas.create_line(gx, y, gx, y + h, fill=guide_color, dash=(4, 4), tags="overlay")
                self.canvas.create_line(x, gy, x + w, gy, fill=guide_color, dash=(4, 4), tags="overlay")

        elif self.grid_mode == "Center Crosshair":
            cx = x + w // 2
            cy = y + h // 2
            # Center target crosshair
            self.canvas.create_line(cx - 30, cy, cx + 30, cy, fill=guide_color, width=2, tags="overlay")
            self.canvas.create_line(cx, cy - 30, cx, cy + 30, fill=guide_color, width=2, tags="overlay")
            self.canvas.create_oval(cx - 20, cy - 20, cx + 20, cy + 20, outline=guide_color, width=1, dash=(2, 2), tags="overlay")

        elif self.grid_mode == "Golden Ratio":
            phi = 0.618033
            g1_x = x + int(w * (1 - phi))
            g2_x = x + int(w * phi)
            g1_y = y + int(h * (1 - phi))
            g2_y = y + int(h * phi)
            self.canvas.create_line(g1_x, y, g1_x, y + h, fill=guide_color, dash=(3, 3), tags="overlay")
            self.canvas.create_line(g2_x, y, g2_x, y + h, fill=guide_color, dash=(3, 3), tags="overlay")
            self.canvas.create_line(x, g1_y, x + w, g1_y, fill=guide_color, dash=(3, 3), tags="overlay")
            self.canvas.create_line(x, g2_y, x + w, g2_y, fill=guide_color, dash=(3, 3), tags="overlay")

    def _draw_telemetry_hud(self, rx1: int, ry1: int, rx2: int, ry2: int, fw: int, fh: int,
                            capture_fps: float, is_recording: bool, is_paused: bool,
                            rec_dur: str, active_filter: str, motion_percent: float, is_security: bool):
        """Draw HUD badges on canvas."""
        # Top-left badge: FPS
        fps_text = f"CAM {capture_fps:4.1f} FPS  |  UI {self.display_fps:4.1f} FPS"
        self.canvas.create_rectangle(rx1 + 10, ry1 + 10, rx1 + 195, ry1 + 34,
                                    fill="#0F172A", outline="#1E293B", tags="overlay")
        self.canvas.create_text(rx1 + 18, ry1 + 22, text=fps_text, anchor=tk.W,
                                fill="#38BDF8", font=("Consolas", 8, "bold"), tags="overlay")

        # Top-right badge: Resolution
        res_text = f"{fw}x{fh} HD"
        tw = 110
        self.canvas.create_rectangle(rx2 - tw - 10, ry1 + 10, rx2 - 10, ry1 + 34,
                                    fill="#0F172A", outline="#1E293B", tags="overlay")
        self.canvas.create_text(rx2 - tw, ry1 + 22, text=res_text, anchor=tk.W,
                                fill="#A78BFA", font=("Consolas", 8, "bold"), tags="overlay")

        # Recording Live Banner
        if is_recording:
            # Pulsing red dot or amber paused tag
            rec_color = "#F59E0B" if is_paused else "#EF4444"
            status_text = f"PAUSED  {rec_dur}" if is_paused else f"REC  {rec_dur}"
            bx1 = (rx1 + rx2) // 2 - 80
            bx2 = (rx1 + rx2) // 2 + 80
            self.canvas.create_rectangle(bx1, ry1 + 10, bx2, ry1 + 36,
                                        fill="#18181B", outline=rec_color, width=2, tags="overlay")
            # Pulsing dot
            self.canvas.create_oval(bx1 + 14, ry1 + 17, bx1 + 26, ry1 + 29,
                                    fill=rec_color, outline="", tags="overlay")
            self.canvas.create_text(bx1 + 36, ry1 + 23, text=status_text, anchor=tk.W,
                                    fill="#FFFFFF", font=("Segoe UI", 9, "bold"), tags="overlay")

        # Security Motion Meter
        if is_security:
            bar_w = 140
            bar_x1 = rx1 + 10
            bar_y1 = ry2 - 32
            self.canvas.create_rectangle(bar_x1, bar_y1, bar_x1 + bar_w, bar_y1 + 18,
                                        fill="#0F172A", outline="#334155", tags="overlay")
            # Filled motion portion
            fill_len = int(min(1.0, motion_percent / 20.0) * (bar_w - 4))
            col = "#EF4444" if motion_percent > 3.5 else "#10B981"
            if fill_len > 0:
                self.canvas.create_rectangle(bar_x1 + 2, bar_y1 + 2, bar_x1 + 2 + fill_len, bar_y1 + 16,
                                            fill=col, outline="", tags="overlay")
            self.canvas.create_text(bar_x1 + bar_w // 2, bar_y1 + 9, text=f"MOTION {motion_percent:3.1f}%",
                                    fill="#FFFFFF", font=("Consolas", 7, "bold"), tags="overlay")

    def _draw_countdown_overlay(self, cx: int, cy: int):
        """Draw prominent glowing countdown numeral."""
        radius = 70
        # Dark translucent backing circle
        self.canvas.create_oval(cx - radius, cy - radius, cx + radius, cy + radius,
                                fill="#0F172A", outline="#00D2FF", width=4, tags="overlay")
        # Big number
        self.canvas.create_text(cx, cy, text=str(self.countdown_val),
                                fill="#FFFFFF", font=("Segoe UI", 48, "bold"), tags="overlay")
