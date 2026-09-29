import os
import sys
import time
import webbrowser
import tkinter as tk
from tkinter import ttk, messagebox
import cv2

from engine.camera_stream import CameraStream
from engine.filter_engine import FilterEngine
from engine.ai_vision import AIVisionSuite
from engine.recorder import MediaRecorder
from engine.audio_cue import AudioCueManager
from ui.theme import StudioTheme
from ui.canvas_viewport import CanvasViewport
from ui.gallery_panel import GalleryPanel
from ui.clipboard_helper import ClipboardHelper


class WebcamStudioApp:
    """
    Webcam Studio Pro - Advanced Vision & Capture Studio Suite
    Next-generation desktop webcam application with real-time AI,
    color grading, MP4 CFR video recording, time-lapse, burst capture,
    and framing overlays.
    """

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Webcam Studio Pro - NextGen Vision & Capture")
        self.root.geometry("1280x820")
        self.root.minsize(980, 680)

        # Bring window to front
        try:
            self.root.lift()
            self.root.attributes("-topmost", True)
            self.root.after(500, lambda: self.root.attributes("-topmost", False))
            self.root.focus_force()
        except Exception:
            pass

        # Apply Theme
        StudioTheme.apply(self.root)

        # Initialize Core Engines
        self.audio = AudioCueManager(enabled=True)
        self.filter_engine = FilterEngine()
        self.ai_vision = AIVisionSuite()
        self.recorder = MediaRecorder()

        # Connect AI security auto-snapshot callback
        self.ai_vision.security_snap_callback = self._on_security_alert

        # Detect physical cameras or activate synthetic pattern
        self.camera_indices = CameraStream.list_cameras()
        initial_cam = self.camera_indices[0] if self.camera_indices else 0

        self.camera_stream = CameraStream(camera_index=initial_cam, target_res=(1280, 720))

        # Photo countdown state
        self.countdown_seconds = 0
        self._countdown_active = False
        self._countdown_target_time = 0.0
        self._countdown_current_sec = 0

        # Fullscreen state
        self.is_fullscreen = False

        # Build UI layout
        self._build_header_bar()
        self._build_main_workspace()
        self._build_bottom_panels()

        # Bind Pro Keyboard Shortcuts
        self._bind_shortcuts()

        # Start master GUI update loop
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.update_loop()

    def _build_header_bar(self):
        """Top navigation and quick studio settings bar."""
        self.header_frame = ttk.Frame(self.root, style="Sidebar.TFrame")
        self.header_frame.pack(fill=tk.X, side=tk.TOP, padx=10, pady=(8, 4))

        # Brand Title
        brand_frame = ttk.Frame(self.header_frame, style="Sidebar.TFrame")
        brand_frame.pack(side=tk.LEFT, padx=(6, 16))

        ttk.Label(brand_frame, text="⚡ WEBCAM STUDIO PRO", style="Title.TLabel").pack(side=tk.LEFT)
        badge = ttk.Label(brand_frame, text="NEXTGEN", style="Badge.TLabel")
        badge.pack(side=tk.LEFT, padx=8)

        # Camera Selector
        ttk.Label(self.header_frame, text="Camera:", style="Sidebar.TLabel").pack(side=tk.LEFT, padx=(10, 4))
        cam_choices = [f"Camera {i}" for i in self.camera_indices] if self.camera_indices else ["Virtual Test Pattern"]
        self.cam_var = tk.StringVar(value=cam_choices[0])
        self.cam_combo = ttk.Combobox(self.header_frame, textvariable=self.cam_var, values=cam_choices,
                                      state="readonly", width=14)
        self.cam_combo.pack(side=tk.LEFT, padx=4)
        self.cam_combo.bind("<<ComboboxSelected>>", self._on_camera_select)

        # Refresh Cameras
        self.btn_refresh_cam = ttk.Button(self.header_frame, text="🔄", style="Small.TButton",
                                           command=self._refresh_cameras)
        self.btn_refresh_cam.pack(side=tk.LEFT, padx=(2, 10))

        # Resolution Selector
        ttk.Label(self.header_frame, text="Res:", style="Sidebar.TLabel").pack(side=tk.LEFT, padx=(8, 4))
        res_options = list(CameraStream.PRESET_RESOLUTIONS.keys())
        self.res_var = tk.StringVar(value="720p HD")
        self.res_combo = ttk.Combobox(self.header_frame, textvariable=self.res_var, values=res_options,
                                      state="readonly", width=14)
        self.res_combo.pack(side=tk.LEFT, padx=4)
        self.res_combo.bind("<<ComboboxSelected>>", self._on_resolution_select)

        # Studio Quick Action Buttons on Right
        right_bar = ttk.Frame(self.header_frame, style="Sidebar.TFrame")
        right_bar.pack(side=tk.RIGHT, padx=6)

        # Audio Sound Toggle
        self.sound_var = tk.BooleanVar(value=True)
        self.btn_sound = ttk.Button(right_bar, text="🔊 Audio", style="Small.TButton", command=self._toggle_audio)
        self.btn_sound.pack(side=tk.LEFT, padx=4)

        # Watermark Toggle
        self.watermark_var = tk.BooleanVar(value=False)
        self.btn_watermark = ttk.Button(right_bar, text="🕒 Time", style="Small.TButton", command=self._toggle_watermark)
        self.btn_watermark.pack(side=tk.LEFT, padx=4)

        # Grid Toggle
        self.btn_grid = ttk.Button(right_bar, text="📐 Grid", style="Small.TButton", command=self._cycle_grid)
        self.btn_grid.pack(side=tk.LEFT, padx=4)

        # Fullscreen Toggle
        self.btn_fs = ttk.Button(right_bar, text="⛶ Fullscreen", style="Small.TButton", command=self.toggle_fullscreen)
        self.btn_fs.pack(side=tk.LEFT, padx=4)

    def _build_main_workspace(self):
        """Build center split view: Sidebar Notebook and Viewport Canvas."""
        self.workspace = ttk.Frame(self.root, style="TFrame")
        self.workspace.pack(fill=tk.BOTH, expand=True, padx=10, pady=4)

        # Left Controls Sidebar (Notebook)
        self.sidebar_frame = ttk.Frame(self.workspace, style="Sidebar.TFrame", width=340)
        self.sidebar_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        self.sidebar_frame.pack_propagate(False)

        # Notebook tabs
        self.notebook = ttk.Notebook(self.sidebar_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        self.tab_capture = ttk.Frame(self.notebook, style="Sidebar.TFrame")
        self.tab_filters = ttk.Frame(self.notebook, style="Sidebar.TFrame")
        self.tab_ai = ttk.Frame(self.notebook, style="Sidebar.TFrame")
        self.tab_shortcuts = ttk.Frame(self.notebook, style="Sidebar.TFrame")

        self.notebook.add(self.tab_capture, text="📷 Capture")
        self.notebook.add(self.tab_filters, text="🎨 Effects")
        self.notebook.add(self.tab_ai, text="🤖 AI Vision")
        self.notebook.add(self.tab_shortcuts, text="⚙ Settings")

        self._populate_capture_tab()
        self._populate_filters_tab()
        self._populate_ai_tab()
        self._populate_settings_tab()

        # Right Video Viewport Canvas
        self.viewport = CanvasViewport(self.workspace, on_pan_callback=self._on_pan_change)
        self.viewport.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

    def _populate_capture_tab(self):
        """Populate Capture tab with Photo, Video, Burst, Timelapse, and Timer controls."""
        p = self.tab_capture

        # Quick Actions Card
        card_quick = ttk.Frame(p, style="Card.TFrame")
        card_quick.pack(fill=tk.X, padx=8, pady=8)

        ttk.Label(card_quick, text="PRIMARY CAPTURE", style="Subheader.TLabel").pack(anchor=tk.W, padx=10, pady=(10, 6))

        # Big Take Photo Button
        self.btn_photo = ttk.Button(card_quick, text="📸 TAKE PHOTO  [Space]", style="Photo.TButton",
                                    command=self.handle_photo_button)
        self.btn_photo.pack(fill=tk.X, padx=10, pady=6)

        # Self-Timer Options
        timer_box = ttk.Frame(card_quick, style="Card.TFrame")
        timer_box.pack(fill=tk.X, padx=10, pady=4)
        ttk.Label(timer_box, text="Self-Timer:", style="Muted.TLabel").pack(side=tk.LEFT)
        self.timer_var = tk.StringVar(value="Off")
        for opt in ("Off", "3s", "5s", "10s"):
            ttk.Radiobutton(timer_box, text=opt, variable=self.timer_var, value=opt).pack(side=tk.LEFT, padx=3)

        # Video Recording Button
        self.btn_record = ttk.Button(card_quick, text="🔴 START RECORDING  [R]", style="Record.TButton",
                                     command=self.toggle_recording)
        self.btn_record.pack(fill=tk.X, padx=10, pady=(10, 4))

        # Pause / Resume Button
        self.btn_pause = ttk.Button(card_quick, text="⏸ PAUSE RECORDING  [P]", style="TButton",
                                    command=self.toggle_pause, state="disabled")
        self.btn_pause.pack(fill=tk.X, padx=10, pady=(2, 10))

        # Advanced Capture Card (Burst & Timelapse)
        card_adv = ttk.Frame(p, style="Card.TFrame")
        card_adv.pack(fill=tk.X, padx=8, pady=6)

        ttk.Label(card_adv, text="ADVANCED CAPTURE MODES", style="Subheader.TLabel").pack(anchor=tk.W, padx=10, pady=(10, 6))

        # Burst Mode
        burst_frame = ttk.Frame(card_adv, style="Card.TFrame")
        burst_frame.pack(fill=tk.X, padx=10, pady=4)
        self.burst_count_var = tk.IntVar(value=3)
        ttk.Label(burst_frame, text="Burst:", style="Muted.TLabel").pack(side=tk.LEFT)
        for count in (3, 5, 10):
            ttk.Radiobutton(burst_frame, text=f"{count}x", variable=self.burst_count_var, value=count).pack(side=tk.LEFT, padx=4)

        self.btn_burst = ttk.Button(card_adv, text="⚡ Take Burst  [B]", style="Primary.TButton",
                                    command=self.take_burst_capture)
        self.btn_burst.pack(fill=tk.X, padx=10, pady=4)

        # Time-Lapse Mode
        ttk.Separator(card_adv, orient="horizontal").pack(fill=tk.X, padx=10, pady=8)

        tl_frame = ttk.Frame(card_adv, style="Card.TFrame")
        tl_frame.pack(fill=tk.X, padx=10, pady=2)
        ttk.Label(tl_frame, text="Time-Lapse Interval:", style="Muted.TLabel").pack(side=tk.LEFT)
        self.timelapse_interval_var = tk.StringVar(value="5s")
        self.tl_combo = ttk.Combobox(tl_frame, textvariable=self.timelapse_interval_var,
                                     values=["1s", "2s", "5s", "10s", "30s"], width=6, state="readonly")
        self.tl_combo.pack(side=tk.RIGHT)

        self.btn_timelapse = ttk.Button(card_adv, text="⏱ Start Time-Lapse", style="TButton",
                                        command=self.toggle_timelapse)
        self.btn_timelapse.pack(fill=tk.X, padx=10, pady=(6, 10))

        # Format card
        card_fmt = ttk.Frame(p, style="Card.TFrame")
        card_fmt.pack(fill=tk.X, padx=8, pady=6)
        fmt_frame = ttk.Frame(card_fmt, style="Card.TFrame")
        fmt_frame.pack(fill=tk.X, padx=10, pady=8)
        ttk.Label(fmt_frame, text="Photo Format:", style="Muted.TLabel").pack(side=tk.LEFT)
        self.format_var = tk.StringVar(value="PNG")
        for fmt in ("PNG", "JPG"):
            ttk.Radiobutton(fmt_frame, text=fmt, variable=self.format_var, value=fmt).pack(side=tk.LEFT, padx=6)

    def _populate_filters_tab(self):
        """Populate Effects tab with 17 Filters, Sliders, and Geometric Transforms."""
        p = self.tab_filters

        # Scrollable container for effects
        canvas_scroll = tk.Canvas(p, bg="#141622", highlightthickness=0, bd=0)
        scrollbar = ttk.Scrollbar(p, orient="vertical", command=canvas_scroll.yview)
        scroll_content = ttk.Frame(canvas_scroll, style="Sidebar.TFrame")

        scroll_content.bind("<Configure>", lambda e: canvas_scroll.configure(scrollregion=canvas_scroll.bbox("all")))
        canvas_scroll.create_window((0, 0), window=scroll_content, anchor="nw")
        canvas_scroll.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas_scroll.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Filters Card
        card_f = ttk.Frame(scroll_content, style="Card.TFrame")
        card_f.pack(fill=tk.X, padx=6, pady=6)

        ttk.Label(card_f, text="ARTISTIC PRESETS", style="Subheader.TLabel").pack(anchor=tk.W, padx=10, pady=(10, 6))

        self.filter_var = tk.StringVar(value="Normal")
        self.filter_combo = ttk.Combobox(card_f, textvariable=self.filter_var,
                                         values=FilterEngine.AVAILABLE_FILTERS, state="readonly")
        self.filter_combo.pack(fill=tk.X, padx=10, pady=(2, 10))
        self.filter_combo.bind("<<ComboboxSelected>>", self._on_filter_change)

        # Adjustments Card
        card_adj = ttk.Frame(scroll_content, style="Card.TFrame")
        card_adj.pack(fill=tk.X, padx=6, pady=6)

        ttk.Label(card_adj, text="STUDIO COLOR GRADING", style="Subheader.TLabel").pack(anchor=tk.W, padx=10, pady=(10, 4))

        # Sliders: Brightness, Contrast, Saturation, Sharpness, Warmth, Zoom
        self.slider_bright = self._create_slider_row(card_adj, "Brightness", -100, 100, 0, self._on_adjust_change)
        self.slider_contrast = self._create_slider_row(card_adj, "Contrast", 0.5, 2.5, 1.0, self._on_adjust_change)
        self.slider_sat = self._create_slider_row(card_adj, "Saturation", 0.0, 2.5, 1.0, self._on_adjust_change)
        self.slider_sharp = self._create_slider_row(card_adj, "Sharpness", 0.0, 10.0, 0.0, self._on_adjust_change)
        self.slider_warm = self._create_slider_row(card_adj, "Warmth / Tint", -50, 50, 0, self._on_adjust_change)
        self.slider_zoom = self._create_slider_row(card_adj, "Digital Zoom", 1.0, 4.0, 1.0, self._on_adjust_change)

        # Reset button
        ttk.Button(card_adj, text="↺ Reset Grading", style="Small.TButton",
                   command=self._reset_adjustments).pack(fill=tk.X, padx=10, pady=(6, 10))

        # Transforms Card
        card_tr = ttk.Frame(scroll_content, style="Card.TFrame")
        card_tr.pack(fill=tk.X, padx=6, pady=6)

        ttk.Label(card_tr, text="CAMERA ORIENTATION", style="Subheader.TLabel").pack(anchor=tk.W, padx=10, pady=(10, 4))

        self.mirror_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(card_tr, text="🪞 Mirror Mode (Selfie) [M]", variable=self.mirror_var,
                        command=self._on_transform_change).pack(anchor=tk.W, padx=10, pady=2)

        self.flipv_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(card_tr, text="↕ Flip Vertical", variable=self.flipv_var,
                        command=self._on_transform_change).pack(anchor=tk.W, padx=10, pady=2)

        rotate_frame = ttk.Frame(card_tr, style="Card.TFrame")
        rotate_frame.pack(fill=tk.X, padx=10, pady=(4, 10))
        ttk.Label(rotate_frame, text="Rotation:", style="Muted.TLabel").pack(side=tk.LEFT)
        self.rot_var = tk.IntVar(value=0)
        for deg in (0, 90, 180, 270):
            ttk.Radiobutton(rotate_frame, text=f"{deg}°", variable=self.rot_var, value=deg,
                            command=self._on_transform_change).pack(side=tk.LEFT, padx=3)

    def _create_slider_row(self, parent, label_text, min_val, max_val, default_val, callback):
        frame = ttk.Frame(parent, style="Card.TFrame")
        frame.pack(fill=tk.X, padx=10, pady=3)

        header = ttk.Frame(frame, style="Card.TFrame")
        header.pack(fill=tk.X)
        lbl = ttk.Label(header, text=label_text, style="Muted.TLabel")
        lbl.pack(side=tk.LEFT)
        val_lbl = ttk.Label(header, text=f"{default_val:.1f}" if isinstance(default_val, float) else f"{default_val}",
                            style="Muted.TLabel")
        val_lbl.pack(side=tk.RIGHT)

        scale = ttk.Scale(frame, from_=min_val, to=max_val, value=default_val, orient="horizontal",
                          style="Horizontal.TScale")
        scale.pack(fill=tk.X, pady=(2, 0))

        def _on_move(val):
            fval = float(val)
            val_lbl.config(text=f"{fval:.1f}" if (max_val - min_val <= 10) else f"{int(fval)}")
            callback()

        scale.configure(command=_on_move)
        scale.val_label = val_lbl
        return scale

    def _populate_ai_tab(self):
        """Populate AI Vision tab with Face Tracking, Privacy Anonymizer, AR Props, QR, and Motion Guard."""
        p = self.tab_ai

        # Face Tracking Card
        card_face = ttk.Frame(p, style="Card.TFrame")
        card_face.pack(fill=tk.X, padx=8, pady=6)

        ttk.Label(card_face, text="FACE & SUBJECT TRACKING", style="Subheader.TLabel").pack(anchor=tk.W, padx=10, pady=(10, 6))

        self.face_track_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(card_face, text="🎯 Cyber HUD Face Tracking", variable=self.face_track_var,
                        command=self._on_ai_change).pack(anchor=tk.W, padx=10, pady=4)

        # Privacy Anonymizer
        ttk.Separator(card_face, orient="horizontal").pack(fill=tk.X, padx=10, pady=6)
        ttk.Label(card_face, text="Privacy Anonymizer:", style="Muted.TLabel").pack(anchor=tk.W, padx=10)

        self.privacy_var = tk.StringVar(value="None")
        for mode in ("None", "Blur", "Pixelate"):
            ttk.Radiobutton(card_face, text=mode, variable=self.privacy_var, value=mode,
                            command=self._on_ai_change).pack(anchor=tk.W, padx=16, pady=2)

        # AR Props
        ttk.Separator(card_face, orient="horizontal").pack(fill=tk.X, padx=10, pady=6)
        ttk.Label(card_face, text="Augmented Reality Props:", style="Muted.TLabel").pack(anchor=tk.W, padx=10)

        self.ar_var = tk.StringVar(value="None")
        for prop in ("None", "Sunglasses", "Crown", "Mustache"):
            ttk.Radiobutton(card_face, text=prop, variable=self.ar_var, value=prop,
                            command=self._on_ai_change).pack(anchor=tk.W, padx=16, pady=2)

        # Smart Scanner Card (QR / Barcode)
        card_qr = ttk.Frame(p, style="Card.TFrame")
        card_qr.pack(fill=tk.X, padx=8, pady=6)

        ttk.Label(card_qr, text="SMART SCANNER (QR & BARCODES)", style="Subheader.TLabel").pack(anchor=tk.W, padx=10, pady=(10, 6))

        self.qr_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(card_qr, text="🔍 Real-Time QR Scanner", variable=self.qr_var,
                        command=self._on_ai_change).pack(anchor=tk.W, padx=10, pady=4)

        self.qr_payload_label = ttk.Label(card_qr, text="No QR code in frame", style="Muted.TLabel", wraplength=280)
        self.qr_payload_label.pack(fill=tk.X, padx=10, pady=2)

        qr_actions = ttk.Frame(card_qr, style="Card.TFrame")
        qr_actions.pack(fill=tk.X, padx=10, pady=(4, 10))
        self.btn_copy_qr = ttk.Button(qr_actions, text="📋 Copy", style="Small.TButton",
                                      command=self._copy_qr_payload, state="disabled")
        self.btn_copy_qr.pack(side=tk.LEFT, padx=(0, 4))
        self.btn_open_qr = ttk.Button(qr_actions, text="🌐 Open Link", style="Small.TButton",
                                      command=self._open_qr_payload, state="disabled")
        self.btn_open_qr.pack(side=tk.LEFT)

        # Motion Detection & Security Guard Card
        card_sec = ttk.Frame(p, style="Card.TFrame")
        card_sec.pack(fill=tk.X, padx=8, pady=6)

        ttk.Label(card_sec, text="MOTION & SECURITY GUARD", style="Subheader.TLabel").pack(anchor=tk.W, padx=10, pady=(10, 6))

        self.motion_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(card_sec, text="🚨 Motion Heatmap & Contours", variable=self.motion_var,
                        command=self._on_ai_change).pack(anchor=tk.W, padx=10, pady=2)

        self.security_guard_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(card_sec, text="🛡 Auto-Snapshot on Motion", variable=self.security_guard_var,
                        command=self._on_ai_change).pack(anchor=tk.W, padx=10, pady=2)

        # Sensitivity slider
        sec_thresh_frame = ttk.Frame(card_sec, style="Card.TFrame")
        sec_thresh_frame.pack(fill=tk.X, padx=10, pady=(4, 10))
        ttk.Label(sec_thresh_frame, text="Sensitivity Threshold:", style="Muted.TLabel").pack(anchor=tk.W)
        self.scale_security = ttk.Scale(sec_thresh_frame, from_=1.0, to=15.0, value=3.5,
                                        orient="horizontal", command=self._on_security_thresh_change)
        self.scale_security.pack(fill=tk.X, pady=2)

    def _populate_settings_tab(self):
        """Populate Settings tab with Keyboard Shortcuts and Architecture Specs."""
        p = self.tab_shortcuts

        card_keys = ttk.Frame(p, style="Card.TFrame")
        card_keys.pack(fill=tk.X, padx=8, pady=8)

        ttk.Label(card_keys, text="KEYBOARD SHORTCUTS", style="Subheader.TLabel").pack(anchor=tk.W, padx=10, pady=(10, 6))

        shortcuts = [
            ("Space", "Take Photo / Start Countdown"),
            ("R", "Start / Stop Video Recording"),
            ("P", "Pause / Resume Recording"),
            ("B", "Take Burst Snapshot (3x/5x)"),
            ("M", "Toggle Selfie Mirror Mode"),
            ("G", "Cycle Composition Grids"),
            ("F / F11", "Toggle Fullscreen Mode"),
            ("Escape", "Exit Fullscreen"),
            ("S", "Toggle Audio Cues (Mute)")
        ]

        for key, desc in shortcuts:
            row = ttk.Frame(card_keys, style="Card.TFrame")
            row.pack(fill=tk.X, padx=10, pady=2)
            ttk.Label(row, text=key, font=("Consolas", 9, "bold"), foreground="#00D2FF", width=10).pack(side=tk.LEFT)
            ttk.Label(row, text=desc, style="Muted.TLabel").pack(side=tk.LEFT)

        # Specs Card
        card_specs = ttk.Frame(p, style="Card.TFrame")
        card_specs.pack(fill=tk.X, padx=8, pady=6)

        ttk.Label(card_specs, text="SYSTEM & ENGINE SPECS", style="Subheader.TLabel").pack(anchor=tk.W, padx=10, pady=(10, 6))
        ttk.Label(card_specs, text="• Capture Backend: Windows DirectShow (CAP_DSHOW)", style="Muted.TLabel").pack(anchor=tk.W, padx=10, pady=2)
        ttk.Label(card_specs, text="• Video Codec: MP4 CFR (mp4v)", style="Muted.TLabel").pack(anchor=tk.W, padx=10, pady=2)
        ttk.Label(card_specs, text="• Vision Acceleration: SIMD Downscaled Haar + EMA", style="Muted.TLabel").pack(anchor=tk.W, padx=10, pady=2)
        ttk.Label(card_specs, text="• Zero-Flicker Double Buffered Canvas", style="Muted.TLabel").pack(anchor=tk.W, padx=10, pady=2)

    def _build_bottom_panels(self):
        """Build Media Gallery drawer and Status Bar."""
        # Media Gallery Panel
        self.gallery = GalleryPanel(self.root, on_status_msg=self.set_status)
        self.gallery.pack(fill=tk.X, side=tk.BOTTOM, padx=10, pady=(0, 4))

        # Status Bar
        self.statusbar = ttk.Frame(self.root, style="CardLight.TFrame")
        self.statusbar.pack(fill=tk.X, side=tk.BOTTOM, padx=10, pady=(0, 2))

        self.status_label = ttk.Label(self.statusbar, text="Studio ready • Press Space to capture",
                                      style="Muted.TLabel")
        self.status_label.pack(side=tk.LEFT, padx=8, pady=3)

        self.status_rec_label = ttk.Label(self.statusbar, text="", foreground="#EF4444",
                                          font=("Segoe UI", 9, "bold"))
        self.status_rec_label.pack(side=tk.RIGHT, padx=10, pady=3)

    def _bind_shortcuts(self):
        """Map pro hotkeys to window."""
        self.root.bind("<space>", lambda e: self.handle_photo_button())
        self.root.bind("<r>", lambda e: self.toggle_recording())
        self.root.bind("<R>", lambda e: self.toggle_recording())
        self.root.bind("<p>", lambda e: self.toggle_pause())
        self.root.bind("<P>", lambda e: self.toggle_pause())
        self.root.bind("<b>", lambda e: self.take_burst_capture())
        self.root.bind("<B>", lambda e: self.take_burst_capture())
        self.root.bind("<m>", lambda e: self._toggle_mirror_hotkey())
        self.root.bind("<M>", lambda e: self._toggle_mirror_hotkey())
        self.root.bind("<g>", lambda e: self._cycle_grid())
        self.root.bind("<G>", lambda e: self._cycle_grid())
        self.root.bind("<s>", lambda e: self._toggle_audio())
        self.root.bind("<S>", lambda e: self._toggle_audio())
        self.root.bind("<F11>", lambda e: self.toggle_fullscreen())
        self.root.bind("<Escape>", lambda e: self.exit_fullscreen())

    def set_status(self, text: str):
        """Update bottom status text."""
        self.status_label.config(text=text)

    # ------------------ Camera & Stream Controls ------------------

    def _refresh_cameras(self):
        """Re-scan physical devices and update dropdown."""
        self.camera_indices = CameraStream.list_cameras()
        cam_choices = [f"Camera {i}" for i in self.camera_indices] if self.camera_indices else ["Virtual Test Pattern"]
        self.cam_combo.config(values=cam_choices)
        if cam_choices:
            self.cam_var.set(cam_choices[0])
            self._on_camera_select(None)
        self.set_status(f"Devices scanned: {len(self.camera_indices)} camera(s) detected.")

    def _on_camera_select(self, event):
        sel = self.cam_var.get()
        if "Camera" in sel:
            idx = int(sel.split()[-1])
            self.camera_stream.switch_camera(idx)
            self.set_status(f"Switched to device {sel}")
        else:
            self.camera_stream.switch_camera(999)  # Triggers synthetic pattern
            self.set_status("Switched to Virtual Test Pattern")

    def _on_resolution_select(self, event):
        sel = self.res_var.get()
        if sel in CameraStream.PRESET_RESOLUTIONS:
            w, h = CameraStream.PRESET_RESOLUTIONS[sel]
            actual_w, actual_h = self.camera_stream.set_resolution(w, h)
            self.set_status(f"Resolution adjusted to {actual_w}x{actual_h}")

    def _toggle_audio(self):
        self.audio.enabled = not self.audio.enabled
        self.btn_sound.config(text="🔊 Audio" if self.audio.enabled else "🔇 Muted")
        self.set_status("Audio cues enabled" if self.audio.enabled else "Audio cues muted")

    def _toggle_watermark(self):
        self.viewport.show_watermark = not self.viewport.show_watermark
        self.set_status("Timestamp watermark enabled" if self.viewport.show_watermark else "Watermark disabled")

    def _cycle_grid(self):
        mode = self.viewport.cycle_grid_mode()
        self.btn_grid.config(text=f"📐 {mode[:8]}")
        self.set_status(f"Framing grid: {mode}")

    def toggle_fullscreen(self):
        self.is_fullscreen = not self.is_fullscreen
        self.root.attributes("-fullscreen", self.is_fullscreen)
        self.btn_fs.config(text="🗗 Windowed" if self.is_fullscreen else "⛶ Fullscreen")

    def exit_fullscreen(self):
        if self.is_fullscreen:
            self.is_fullscreen = False
            self.root.attributes("-fullscreen", False)
            self.btn_fs.config(text="⛶ Fullscreen")

    # ------------------ Filter & Grading Handlers ------------------

    def _on_filter_change(self, event):
        self.filter_engine.current_filter = self.filter_var.get()
        self.set_status(f"Applied preset: {self.filter_var.get()}")

    def _on_adjust_change(self):
        self.filter_engine.brightness = self.slider_bright.get()
        self.filter_engine.contrast = self.slider_contrast.get()
        self.filter_engine.saturation = self.slider_sat.get()
        self.filter_engine.sharpness = self.slider_sharp.get()
        self.filter_engine.warmth = self.slider_warm.get()
        self.filter_engine.zoom_level = self.slider_zoom.get()

    def _on_pan_change(self, dx: float, dy: float):
        if self.filter_engine.zoom_level > 1.05:
            self.filter_engine.pan_x = max(-1.0, min(1.0, self.filter_engine.pan_x + dx))
            self.filter_engine.pan_y = max(-1.0, min(1.0, self.filter_engine.pan_y + dy))

    def _reset_adjustments(self):
        self.filter_engine.reset_adjustments()
        self.slider_bright.set(0)
        self.slider_contrast.set(1.0)
        self.slider_sat.set(1.0)
        self.slider_sharp.set(0.0)
        self.slider_warm.set(0)
        self.slider_zoom.set(1.0)
        for s in (self.slider_bright, self.slider_contrast, self.slider_sat,
                  self.slider_sharp, self.slider_warm, self.slider_zoom):
            s.val_label.config(text=f"{s.get():.1f}")
        self.set_status("Color grading and digital zoom reset to default.")

    def _on_transform_change(self):
        self.filter_engine.flip_h = self.mirror_var.get()
        self.filter_engine.flip_v = self.flipv_var.get()
        self.filter_engine.rotation_degrees = self.rot_var.get()

    def _toggle_mirror_hotkey(self):
        self.mirror_var.set(not self.mirror_var.get())
        self._on_transform_change()
        self.set_status("Mirror mode ON" if self.mirror_var.get() else "Mirror mode OFF")

    # ------------------ AI Vision Handlers ------------------

    def _on_ai_change(self):
        self.ai_vision.face_tracking_enabled = self.face_track_var.get()
        self.ai_vision.privacy_mode = self.privacy_var.get()
        self.ai_vision.ar_prop = self.ar_var.get()
        self.ai_vision.qr_scanner_enabled = self.qr_var.get()
        self.ai_vision.motion_enabled = self.motion_var.get()
        self.ai_vision.security_guard_enabled = self.security_guard_var.get()

    def _on_security_thresh_change(self, val):
        self.ai_vision.security_threshold = float(val)

    def _on_security_alert(self, msg: str):
        ret, frame = self.camera_stream.get_frame()
        if ret and frame is not None:
            # Process with active filters
            processed = self.filter_engine.process(frame)
            saved = self.recorder.take_snapshot(processed, file_format="jpg", prefix="security_alert")
            self.audio.play_shutter_click()
            self.set_status(f"Security Auto-Snapshot saved: {os.path.basename(saved)}")
            self.gallery.refresh_gallery()

    def _copy_qr_payload(self):
        text = self.ai_vision.last_qr_text
        if text:
            ClipboardHelper.copy_text(text)
            self.set_status(f"Copied QR payload: {text}")

    def _open_qr_payload(self):
        text = self.ai_vision.last_qr_text
        if text:
            if text.startswith(("http://", "https://")):
                webbrowser.open(text)
                self.set_status(f"Opened URL in browser: {text}")
            else:
                self.set_status(f"QR payload is not a URL: {text}")

    # ------------------ Capture & Recording Handlers ------------------

    def handle_photo_button(self):
        timer_str = self.timer_var.get()
        if timer_str == "Off" or self._countdown_active:
            self._execute_photo_capture()
        else:
            sec = int(timer_str.replace("s", ""))
            self._start_countdown(sec)

    def _start_countdown(self, seconds: int):
        self.countdown_seconds = seconds
        self._countdown_active = True
        self._countdown_target_time = time.time() + seconds
        self._countdown_current_sec = seconds
        self.viewport.set_countdown(seconds)
        self.audio.play_countdown_tick()
        self.set_status(f"Self-Timer: {seconds}s countdown...")

    def _execute_photo_capture(self):
        ret, frame = self.camera_stream.get_frame()
        if not ret or frame is None:
            return

        # Apply active filter & AI
        processed = self.filter_engine.process(frame)
        processed = self.ai_vision.process(processed)

        # Trigger visual shutter flash & sound
        self.viewport.trigger_flash()
        self.audio.play_shutter_click()

        # Save snapshot
        fmt = self.format_var.get().lower()
        filepath = self.recorder.take_snapshot(processed, file_format=fmt)
        self.set_status(f"Photo captured: {os.path.basename(filepath)}")

        # Refresh gallery
        self.root.after(200, self.gallery.refresh_gallery)

    def take_burst_capture(self):
        count = self.burst_count_var.get()
        self.set_status(f"Taking burst capture ({count} shots)...")

        def _burst_step(step):
            if step < count:
                ret, frame = self.camera_stream.get_frame()
                if ret and frame is not None:
                    proc = self.filter_engine.process(frame)
                    proc = self.ai_vision.process(proc)
                    self.viewport.trigger_flash(0.08)
                    self.audio.play_shutter_click()
                    self.recorder.take_snapshot(proc, file_format="jpg", prefix=f"burst_{step+1}of{count}")
                self.root.after(160, lambda: _burst_step(step + 1))
            else:
                self.set_status(f"Burst complete ({count} photos saved).")
                self.gallery.refresh_gallery()

        _burst_step(0)

    def toggle_timelapse(self):
        if not self.recorder.timelapse_active:
            interval_sec = float(self.timelapse_interval_var.get().replace("s", ""))
            folder = self.recorder.start_timelapse(interval_seconds=interval_sec)
            self.btn_timelapse.config(text="⏹ Stop Time-Lapse", style="Record.TButton")
            self.set_status(f"Time-lapse started (every {interval_sec}s) in {os.path.basename(folder)}")
        else:
            folder = self.recorder.stop_timelapse()
            self.btn_timelapse.config(text="⏱ Start Time-Lapse", style="TButton")
            self.set_status(f"Time-lapse stopped. Saved in {os.path.basename(folder) if folder else 'snapshots'}")
            self.gallery.refresh_gallery()

    def toggle_recording(self):
        if not self.recorder.is_recording:
            # Start Recording MP4
            target_w = self.camera_stream.width
            target_h = self.camera_stream.height
            fps = self.camera_stream.fps if self.camera_stream.fps > 10 else 30.0
            video_file = self.recorder.start_recording(target_w, target_h, fps=fps)

            self.btn_record.config(text="⏹ STOP RECORDING  [R]", style="Record.TButton")
            self.btn_pause.config(state="normal", text="⏸ PAUSE RECORDING  [P]")
            self.audio.play_record_start()
            self.set_status(f"Recording MP4: {os.path.basename(video_file)}")
        else:
            # Stop Recording
            video_file = self.recorder.stop_recording()
            self.btn_record.config(text="🔴 START RECORDING  [R]", style="Record.TButton")
            self.btn_pause.config(state="disabled", text="⏸ PAUSE RECORDING  [P]")
            self.audio.play_record_stop()
            self.status_rec_label.config(text="")
            self.set_status(f"Recording saved: {os.path.basename(video_file) if video_file else 'saved'}")
            self.gallery.refresh_gallery()

    def toggle_pause(self):
        if self.recorder.is_recording:
            is_paused = self.recorder.toggle_pause()
            if is_paused:
                self.btn_pause.config(text="▶ RESUME RECORDING  [P]")
                self.set_status("Recording paused.")
            else:
                self.btn_pause.config(text="⏸ PAUSE RECORDING  [P]")
                self.set_status("Recording resumed.")

    # ------------------ Master Update Loop ------------------

    def update_loop(self):
        """High-speed real-time frame acquisition and presentation loop."""
        ret, raw_frame = self.camera_stream.get_frame()

        if ret and raw_frame is not None:
            # 1. Pipeline processing: Filters & Grading -> AI Vision Suite
            processed_frame = self.filter_engine.process(raw_frame)
            processed_frame = self.ai_vision.process(processed_frame)

            # 2. Feed frame to MP4 Video Recorder if recording
            if self.recorder.is_recording:
                self.recorder.feed_video_frame(processed_frame)

            # 3. Check Time-lapse capture interval
            if self.recorder.timelapse_active:
                lapse_file = self.recorder.check_timelapse_tick(processed_frame)
                if lapse_file:
                    self.audio.play_shutter_click()
                    self.set_status(f"Time-lapse frame: {os.path.basename(lapse_file)}")

            # 4. Handle Self-Timer countdown
            if self._countdown_active:
                remaining = self._countdown_target_time - time.time()
                current_sec = int(remaining) + 1
                if current_sec != self._countdown_current_sec and current_sec > 0:
                    self._countdown_current_sec = current_sec
                    self.viewport.set_countdown(current_sec)
                    self.audio.play_countdown_tick()
                elif remaining <= 0:
                    self._countdown_active = False
                    self.viewport.set_countdown(None)
                    self.audio.play_countdown_go()
                    self._execute_photo_capture()

            # 5. Render to high-performance viewport
            rec_dur = self.recorder.get_recording_duration()
            self.viewport.render_frame(
                frame=processed_frame,
                capture_fps=self.camera_stream.fps,
                is_recording=self.recorder.is_recording,
                is_paused=self.recorder.is_paused,
                recording_duration=rec_dur,
                active_filter=self.filter_engine.current_filter,
                motion_percent=self.ai_vision.motion_percent,
                is_security_active=self.ai_vision.security_guard_enabled
            )

            # Update live recording indicator on status bar
            if self.recorder.is_recording:
                state_txt = "PAUSED" if self.recorder.is_paused else "● REC"
                mb = self.recorder.get_recording_size_mb()
                self.status_rec_label.config(text=f"{state_txt}  {rec_dur}  ({mb:.1f} MB)")

            # Update QR banner if QR scanner is active
            if self.ai_vision.qr_scanner_enabled and self.ai_vision.last_qr_text:
                now = time.time()
                if now - self.ai_vision.last_qr_time < 3.0:
                    qtext = self.ai_vision.last_qr_text
                    disp = qtext if len(qtext) < 32 else qtext[:29] + "..."
                    self.qr_payload_label.config(text=f"Detected: {disp}")
                    self.btn_copy_qr.config(state="normal")
                    self.btn_open_qr.config(state="normal" if qtext.startswith(("http://", "https://")) else "disabled")
                else:
                    self.btn_copy_qr.config(state="disabled")
                    self.btn_open_qr.config(state="disabled")

        # Schedule next tick for 60 FPS UI rendering
        self.root.after(16, self.update_loop)

    def on_closing(self):
        """Clean shutdown of all worker threads and devices."""
        try:
            if self.recorder.is_recording:
                self.recorder.stop_recording()
            if self.recorder.timelapse_active:
                self.recorder.stop_timelapse()
            self.camera_stream.release()
        except Exception:
            pass
        self.root.destroy()


def main():
    try:
        root = tk.Tk()
        app = WebcamStudioApp(root)
        root.mainloop()
    except Exception as e:
        import traceback
        with open("app_crash.log", "w") as f:
            traceback.print_exc(file=f)


if __name__ == "__main__":
    main()
