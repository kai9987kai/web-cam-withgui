import os
import sys
import time
import subprocess
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Optional, Callable
import cv2
import numpy as np
from PIL import Image, ImageTk

from engine.point_cloud import PointCloudData, PointCloudGenerator


class PointCloudViewerWidget(ttk.Frame):
    """
    High-Performance Interactive 3D Point Cloud Studio Viewer:
    - Vectorized NumPy 3D orbit rotation & perspective projection (>100 FPS)
    - Mouse orbit (Left-drag), Pan (Right-drag), and Zoom (Scroll)
    - 4 Shading Modes (RGB Photo, Turbo Depth Heatmap, Elevation, 3D Lit Normals)
    - Auto-Rotate Turntable mode
    - 3D Grid floor and orientation gizmo
    - Direct export to .PLY, .OBJ, and 1-click launch in Windows 3D Viewer or Open3D
    """

    def __init__(self, parent, on_status_msg: Optional[Callable[[str], None]] = None, **kwargs):
        super().__init__(parent, style="TFrame", **kwargs)
        self.on_status_msg = on_status_msg

        self.pcd_data: Optional[PointCloudData] = None

        # Camera & Transform state
        self.yaw = 0.0          # Radians (horizontal orbit)
        self.pitch = 0.0        # Radians (vertical orbit)
        self.cam_dist = 2.5     # Distance along Z
        self.pan_x = 0.0
        self.pan_y = 0.0
        self.point_size = 2     # Pixel diameter

        # Shading mode: "RGB Photo", "Depth Heatmap", "Height Elevation", "3D Lit"
        self.shading_mode = "RGB Photo"

        # Turntable auto-rotate
        self.auto_rotate = False
        self._auto_rotate_speed = 0.02

        # Telemetry
        self.render_fps = 0.0
        self._fps_count = 0
        self._fps_time = time.time()

        # Canvas & Image references
        self._photo_ref: Optional[ImageTk.PhotoImage] = None

        # Mouse interaction anchors
        self._last_mouse_x = 0
        self._last_mouse_y = 0

        self._build_ui()
        self._bind_mouse_events()

    def _build_ui(self):
        """Construct toolbar, canvas, and 3D HUD."""
        # Top 3D Control Bar
        self.toolbar = ttk.Frame(self, style="CardLight.TFrame")
        self.toolbar.pack(fill=tk.X, side=tk.TOP, padx=2, pady=2)

        # Shading mode dropdown
        ttk.Label(self.toolbar, text="Shading:", style="Sidebar.TLabel").pack(side=tk.LEFT, padx=(6, 4))
        self.shading_var = tk.StringVar(value="RGB Photo")
        modes = ["RGB Photo", "Depth Heatmap", "Height Elevation", "3D Lit"]
        self.shading_combo = ttk.Combobox(self.toolbar, textvariable=self.shading_var, values=modes,
                                          state="readonly", width=14)
        self.shading_combo.pack(side=tk.LEFT, padx=4)
        self.shading_combo.bind("<<ComboboxSelected>>", self._on_shading_change)

        # Point size
        ttk.Label(self.toolbar, text="Size:", style="Sidebar.TLabel").pack(side=tk.LEFT, padx=(10, 4))
        self.size_var = tk.IntVar(value=2)
        for s in (1, 2, 3, 4):
            ttk.Radiobutton(self.toolbar, text=f"{s}px", variable=self.size_var, value=s,
                            command=self._on_size_change).pack(side=tk.LEFT, padx=2)

        # Camera view presets
        ttk.Button(self.toolbar, text="Front", style="Small.TButton",
                   command=lambda: self.set_view(0, 0)).pack(side=tk.LEFT, padx=(10, 2))
        ttk.Button(self.toolbar, text="Isometric", style="Small.TButton",
                   command=lambda: self.set_view(0.5, 0.4)).pack(side=tk.LEFT, padx=2)
        ttk.Button(self.toolbar, text="Top", style="Small.TButton",
                   command=lambda: self.set_view(0, 1.57)).pack(side=tk.LEFT, padx=2)

        # Turntable button
        self.btn_turntable = ttk.Button(self.toolbar, text="⟳ Auto-Rotate", style="Small.TButton",
                                        command=self.toggle_auto_rotate)
        self.btn_turntable.pack(side=tk.LEFT, padx=8)

        # Right Action Buttons (Export & External Viewers)
        right_actions = ttk.Frame(self.toolbar, style="CardLight.TFrame")
        right_actions.pack(side=tk.RIGHT, padx=6)

        ttk.Button(right_actions, text="💾 Export PLY", style="Small.TButton",
                   command=self.export_ply).pack(side=tk.LEFT, padx=2)
        ttk.Button(right_actions, text="💾 Export OBJ", style="Small.TButton",
                   command=self.export_obj).pack(side=tk.LEFT, padx=2)
        ttk.Button(right_actions, text="👀 Windows 3D", style="Small.TButton",
                   command=self.open_in_windows_3d_viewer).pack(side=tk.LEFT, padx=2)
        ttk.Button(right_actions, text="🚀 Open3D Studio", style="Small.TButton",
                   command=self.open_in_open3d).pack(side=tk.LEFT, padx=2)

        # Main 3D Canvas
        self.canvas = tk.Canvas(self, bg="#0A0B10", highlightthickness=0, bd=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

    def _bind_mouse_events(self):
        """Map mouse drag to rotation and panning."""
        self.canvas.bind("<ButtonPress-1>", self._on_left_down)
        self.canvas.bind("<B1-Motion>", self._on_left_drag)
        self.canvas.bind("<ButtonPress-3>", self._on_right_down)
        self.canvas.bind("<B3-Motion>", self._on_right_drag)
        self.canvas.bind("<MouseWheel>", self._on_scroll)

    def _on_left_down(self, event):
        self._last_mouse_x = event.x
        self._last_mouse_y = event.y

    def _on_left_drag(self, event):
        dx = event.x - self._last_mouse_x
        dy = event.y - self._last_mouse_y
        self.yaw += dx * 0.012
        self.pitch = max(-1.55, min(1.55, self.pitch + dy * 0.012))
        self._last_mouse_x = event.x
        self._last_mouse_y = event.y
        self.render()

    def _on_right_down(self, event):
        self._last_mouse_x = event.x
        self._last_mouse_y = event.y

    def _on_right_drag(self, event):
        dx = event.x - self._last_mouse_x
        dy = event.y - self._last_mouse_y
        self.pan_x += dx * 0.004
        self.pan_y -= dy * 0.004
        self._last_mouse_x = event.x
        self._last_mouse_y = event.y
        self.render()

    def _on_scroll(self, event):
        # Zoom in / out
        if event.delta > 0:
            self.cam_dist = max(0.5, self.cam_dist * 0.90)
        else:
            self.cam_dist = min(10.0, self.cam_dist * 1.10)
        self.render()

    def set_view(self, yaw: float, pitch: float):
        self.yaw = yaw
        self.pitch = pitch
        self.pan_x = 0.0
        self.pan_y = 0.0
        self.cam_dist = 2.5
        self.render()

    def toggle_auto_rotate(self):
        self.auto_rotate = not self.auto_rotate
        self.btn_turntable.config(text="⏹ Stop Rotate" if self.auto_rotate else "⟳ Auto-Rotate")
        if self.auto_rotate:
            self._turntable_step()

    def _turntable_step(self):
        if self.auto_rotate and self.pcd_data is not None:
            self.yaw += self._auto_rotate_speed
            self.render()
            self.after(20, self._turntable_step)

    def _on_shading_change(self, event):
        self.shading_mode = self.shading_var.get()
        self.render()

    def _on_size_change(self):
        self.point_size = self.size_var.get()
        self.render()

    def load_point_cloud(self, pcd_data: PointCloudData):
        """Set active 3D model and render initial view."""
        self.pcd_data = pcd_data
        self.set_view(0.0, 0.0)
        if self.on_status_msg:
            self.on_status_msg(f"3D Model Generated: {pcd_data.num_points:,} points.")

    def render(self):
        """High-performance 3D perspective projection and rasterization."""
        cw = self.canvas.winfo_width()
        ch = self.canvas.winfo_height()
        if cw < 20 or ch < 20:
            return

        # Empty state screen
        if self.pcd_data is None or len(self.pcd_data.points) == 0:
            self.canvas.delete("all")
            self.canvas.create_text(cw // 2, ch // 2 - 20, text="🌐 NO 3D MODEL LOADED",
                                    fill="#64748B", font=("Segoe UI", 16, "bold"))
            self.canvas.create_text(cw // 2, ch // 2 + 15,
                                    text="Click '✨ Capture 3D Point Cloud' in the left sidebar to generate a 3D model",
                                    fill="#475569", font=("Segoe UI", 10))
            return

        t0 = time.perf_counter()
        pts = self.pcd_data.points  # (N, 3)

        # 1. 3D Rotation Matrix (Euler Pitch & Yaw)
        cy, sy = np.cos(self.yaw), np.sin(self.yaw)
        cp, sp = np.cos(self.pitch), np.sin(self.pitch)

        # R = Rx(pitch) @ Ry(yaw)
        # [[cy, 0, sy], [sp*sy, cp, -sp*cy], [-cp*sy, sp, cp*cy]]
        R = np.array([
            [cy, 0.0, sy],
            [sp * sy, cp, -sp * cy],
            [-cp * sy, sp, cp * cy]
        ], dtype=np.float32)

        # Rotate points
        rotated = pts @ R.T

        # Camera translation (pan and zoom distance)
        X = rotated[:, 0] + self.pan_x
        Y = rotated[:, 1] + self.pan_y
        Z = rotated[:, 2] + self.cam_dist

        # Cull points behind camera plane
        valid = Z > 0.1
        X_val, Y_val, Z_val = X[valid], Y[valid], Z[valid]

        # 2. Perspective Projection
        focal = float(min(cw, ch)) * 0.95
        cx, cy_center = cw / 2.0, ch / 2.0
        u = (cx + (X_val / Z_val) * focal).astype(np.int32)
        v = (cy_center - (Y_val / Z_val) * focal).astype(np.int32)

        # Viewport bounds clipping
        in_bounds = (u >= 0) & (u < cw) & (v >= 0) & (v < ch)
        u_screen = u[in_bounds]
        v_screen = v[in_bounds]
        z_screen = Z_val[in_bounds]

        # 3. Color Shading Computation
        colors_rgb = self._compute_shading(valid, in_bounds, z_screen, rotated)

        # 4. Rasterize onto dark studio buffer
        # Create subtle cyber dark background with circular radial glow
        buf = np.zeros((ch, cw, 3), dtype=np.uint8)
        buf[:] = (12, 14, 22)  # Dark obsidian

        # Draw 3D points
        # If point_size == 1: direct vectorized indexing
        # If point_size > 1: stamp pixels
        if self.point_size == 1:
            buf[v_screen, u_screen] = colors_rgb
        else:
            r = self.point_size // 2
            for dy in range(-r, r + 1):
                for dx in range(-r, r + 1):
                    vy = np.clip(v_screen + dy, 0, ch - 1)
                    ux = np.clip(u_screen + dx, 0, cw - 1)
                    buf[vy, ux] = colors_rgb

        # Convert to PIL PhotoImage
        pil_img = Image.fromarray(buf)
        self._photo_ref = ImageTk.PhotoImage(image=pil_img)

        self.canvas.delete("all")
        self.canvas.create_image(cw // 2, ch // 2, anchor=tk.CENTER, image=self._photo_ref)

        # 5. Draw 3D HUD & Stats
        self._draw_hud(cw, ch)

        # Update FPS
        dt = time.perf_counter() - t0
        self._fps_count += 1
        if time.time() - self._fps_time >= 0.5:
            self.render_fps = self._fps_count / (time.time() - self._fps_time)
            self._fps_count = 0
            self._fps_time = time.time()

    def _compute_shading(self, valid: np.ndarray, in_bounds: np.ndarray,
                         z_screen: np.ndarray, rotated: np.ndarray) -> np.ndarray:
        """Compute RGB colors based on active shading mode."""
        if self.shading_mode == "RGB Photo":
            full_rgb = self.pcd_data.colors
            return full_rgb[valid][in_bounds]

        elif self.shading_mode == "Depth Heatmap":
            # Turbo colormap based on distance Z
            z_min, z_max = z_screen.min(), z_screen.max()
            norm_z = (z_screen - z_min) / (z_max - z_min + 1e-5)
            # Map [0, 255]
            depth_u8 = (norm_z * 255).astype(np.uint8)
            heatmap_bgr = cv2.applyColorMap(depth_u8, cv2.COLORMAP_TURBO)[:, 0, :]
            return cv2.cvtColor(heatmap_bgr.reshape(-1, 1, 3), cv2.COLOR_BGR2RGB).reshape(-1, 3)

        elif self.shading_mode == "Height Elevation":
            # Height Y colormap (Plasma)
            y_vals = rotated[valid][in_bounds][:, 1]
            y_min, y_max = y_vals.min(), y_vals.max()
            norm_y = (y_vals - y_min) / (y_max - y_min + 1e-5)
            y_u8 = (norm_y * 255).astype(np.uint8)
            heat_bgr = cv2.applyColorMap(y_u8, cv2.COLORMAP_PLASMA)[:, 0, :]
            return cv2.cvtColor(heat_bgr.reshape(-1, 1, 3), cv2.COLOR_BGR2RGB).reshape(-1, 3)

        elif self.shading_mode == "3D Lit":
            # Virtual sunlight shading
            normals = self.pcd_data.normals
            if normals is not None:
                norm_sub = normals[valid][in_bounds]
                light_dir = np.array([0.3, 0.6, 0.8], dtype=np.float32)
                light_dir /= np.linalg.norm(light_dir)
                intensity = np.clip(np.dot(norm_sub, light_dir), 0.15, 1.0)
                base_col = self.pcd_data.colors[valid][in_bounds].astype(np.float32)
                lit_col = (base_col * intensity[:, np.newaxis]).clip(0, 255).astype(np.uint8)
                return lit_col
            return self.pcd_data.colors[valid][in_bounds]

        return self.pcd_data.colors[valid][in_bounds]

    def _draw_hud(self, cw: int, ch: int):
        """Draw holographic 3D statistics & navigation indicators."""
        # Top-left info box
        pts_count = self.pcd_data.num_points
        dx, dy, dz = self.pcd_data.bounding_box
        info_lines = [
            f"3D POINT CLOUD | {pts_count:,} POINTS",
            f"BBOX: {dx:.2f} x {dy:.2f} x {dz:.2f} m",
            f"VIEW: Yaw {np.degrees(self.yaw):.0f}°  Pitch {np.degrees(self.pitch):.0f}°  Zoom {self.cam_dist:.1f}m",
            f"3D FPS: {self.render_fps:.1f}"
        ]

        self.canvas.create_rectangle(10, 10, 280, 85, fill="#0B0D18", outline="#1E2338")
        for idx, line in enumerate(info_lines):
            col = "#00D2FF" if idx == 0 else "#94A3B8"
            self.canvas.create_text(18, 22 + idx * 16, text=line, anchor=tk.W,
                                    fill=col, font=("Consolas", 8, "bold" if idx == 0 else "normal"))

        # Bottom-right Controls Tip
        tip_text = "Controls: Left-Drag: Orbit | Right-Drag: Pan | Scroll: Zoom"
        self.canvas.create_text(cw - 12, ch - 12, text=tip_text, anchor=tk.SE,
                                fill="#64748B", font=("Segoe UI", 8))

        # Bottom-left 3D Axis Gizmo
        self._draw_axis_gizmo(45, ch - 45)

    def _draw_axis_gizmo(self, gx: int, gy: int):
        """Draw 3D orientation axis widget."""
        axis_len = 24.0
        cy, sy = np.cos(self.yaw), np.sin(self.yaw)
        cp, sp = np.cos(self.pitch), np.sin(self.pitch)
        R = np.array([[cy, 0, sy], [sp * sy, cp, -sp * cy], [-cp * sy, sp, cp * cy]], dtype=np.float32)

        axes = [
            (np.array([1, 0, 0], dtype=np.float32), "#EF4444", "X"),  # X = Red
            (np.array([0, 1, 0], dtype=np.float32), "#10B981", "Y"),  # Y = Green
            (np.array([0, 0, 1], dtype=np.float32), "#3B82F6", "Z")   # Z = Blue
        ]
        for vec, color, label in axes:
            rot_v = vec @ R.T
            ex = int(gx + rot_v[0] * axis_len)
            ey = int(gy - rot_v[1] * axis_len)
            self.canvas.create_line(gx, gy, ex, ey, fill=color, width=2)
            self.canvas.create_text(ex + 4, ey, text=label, fill=color, font=("Consolas", 7, "bold"))

    # ---------------- Export & Integration Handlers ----------------

    def export_ply(self):
        """Prompt user and save point cloud as .PLY."""
        if not self.pcd_data:
            messagebox.showwarning("Notice", "No 3D point cloud available to export.")
            return

        timestamp = time.strftime("%Y%m%d_%H%M%S")
        default_name = f"pointcloud_{timestamp}.ply"
        path = filedialog.asksaveasfilename(
            defaultextension=".ply",
            filetypes=[("Stanford Point Cloud", "*.ply")],
            initialfile=default_name,
            initialdir="models"
        )
        if path:
            PointCloudGenerator.export_ply(path, self.pcd_data)
            if self.on_status_msg:
                self.on_status_msg(f"Exported PLY: {os.path.basename(path)}")
            messagebox.showinfo("Export Successful", f"Saved 3D Point Cloud to:\n{path}")

    def export_obj(self):
        """Prompt user and save point cloud as .OBJ."""
        if not self.pcd_data:
            messagebox.showwarning("Notice", "No 3D point cloud available to export.")
            return

        timestamp = time.strftime("%Y%m%d_%H%M%S")
        default_name = f"model_{timestamp}.obj"
        path = filedialog.asksaveasfilename(
            defaultextension=".obj",
            filetypes=[("Wavefront 3D Object", "*.obj")],
            initialfile=default_name,
            initialdir="models"
        )
        if path:
            PointCloudGenerator.export_obj(path, self.pcd_data)
            if self.on_status_msg:
                self.on_status_msg(f"Exported OBJ: {os.path.basename(path)}")
            messagebox.showinfo("Export Successful", f"Saved 3D Model to:\n{path}")

    def open_in_windows_3d_viewer(self):
        """Export temporary PLY and launch Windows 3D Viewer or default 3D app."""
        if not self.pcd_data:
            messagebox.showwarning("Notice", "No 3D point cloud available.")
            return

        os.makedirs("models", exist_ok=True)
        temp_path = os.path.abspath("models/live_preview.ply")
        PointCloudGenerator.export_ply(temp_path, self.pcd_data)

        try:
            if sys.platform.startswith("win"):
                os.startfile(temp_path)
            elif sys.platform.startswith("darwin"):
                subprocess.Popen(["open", temp_path])
            else:
                subprocess.Popen(["xdg-open", temp_path])
            if self.on_status_msg:
                self.on_status_msg("Opened in system 3D Viewer.")
        except Exception as e:
            messagebox.showerror("Error", f"Could not launch system 3D viewer: {e}")

    def open_in_open3d(self):
        """Launch GPU-accelerated interactive C++ Open3D window."""
        if not self.pcd_data:
            messagebox.showwarning("Notice", "No 3D point cloud available.")
            return
        ok = PointCloudGenerator.open_in_open3d_studio(self.pcd_data)
        if ok and self.on_status_msg:
            self.on_status_msg("Launched interactive Open3D Studio window.")
