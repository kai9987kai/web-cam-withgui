# ⚡ Webcam Studio Pro (NextGen Vision & Capture)

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![OpenCV](https://img.shields.io/badge/OpenCV-4.14-green.svg)](https://opencv.org/)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)]()
[![License](https://img.shields.io/badge/License-MIT-purple.svg)](LICENSE)

An advanced, pro-grade desktop webcam studio application built with **OpenCV**, **PIL**, and a modern **Obsidian Dark Tkinter UI**. Designed for content creators, security monitoring, video calls, and computer vision enthusiasts.

---

## 🌟 Key Innovations & Major Advancements

### 1. 🚀 High-Performance Capture Engine
- **DirectShow Acceleration (`CAP_DSHOW`)**: Instant webcam initialization on Windows with zero startup lag.
- **Dynamic Resolution Negotiation**: Seamless switching between **1080p Full HD**, **720p HD**, **480p SD**, and **360p Compact**.
- **Dual Telemetry FPS Tracking**: Independent calculation of physical hardware capture FPS and display rendering FPS.
- **Fail-Safe Synthetic Test Pattern**: If a physical camera is disconnected or busy, automatically generates a professional SMPTE color bar test card with live timecode and animated radar so the studio never crashes.

### 2. 🎨 17 Studio Color Grading & Artistic Filters
- **Vectorized Color Matrix Filters**:
  - `Normal` (Original uncompressed)
  - `Grayscale` & `Noir` (High-contrast film S-curve)
  - `Sepia` (Authentic warm vintage BGR float32 transform)
  - `Cyberpunk` (Neon magenta shadows & electric cyan highlights)
  - `Matrix` (Phosphor green terminal tint)
  - `Sunset Amber` (Golden hour warmth)
  - `Ocean Teal` (Modern cinematic teal)
  - `Thermal` (Infrared false-color Jet mapping)
  - `Night Vision` (Amplified green with CRT phosphor scanlines)
  - `Cartoon` (Bilateral color filtering with adaptive edge lines)
  - `Pencil Sketch` (Detailed artist sketching)
  - `Edges` (Neon glowing Canny contours)
  - `Blur` (Simulated bokeh depth)
  - `Pixelate` (8-bit retro arcade mosaic)
  - `Invert` (Negative color spectrum)
  - `Beauty` (Domain-preserving skin smoothing while retaining crisp eye details)
- **Live Studio Sliders**:
  - Brightness (-100 to +100)
  - Contrast (0.5x to 2.5x)
  - Saturation (0.0x to 2.5x)
  - Sharpness (0 to 10 Unsharp Mask)
  - Warmth / Tint (-50 cool blue to +50 warm amber)
  - Digital Zoom (1.0x to 4.0x) with interactive mouse drag-to-pan!
- **Orientation Transforms**:
  - Horizontal Selfie Mirror (`M`)
  - Vertical Inversion
  - 90° Clockwise Rotation steps

### 3. 🤖 AI & Computer Vision Suite
- **Cyber HUD Face Tracking**:
  - 100x speedup via downscaled pyramid Haar cascade inference.
  - **Exponential Moving Average (EMA)** temporal smoothing to eliminate bounding-box jitter.
  - Sleek high-tech corner brackets and target reticle.
- **Privacy Anonymizer**: Real-time Gaussian Face Blur or Mosaic Pixelation for privacy on streams and calls.
- **Dynamic AR Props**:
  - 🕶️ **Cyberpunk Shades**: Neon glasses fitted to eye coordinates.
  - 👑 **Royal Crown**: Golden crown with ruby and sapphire jewels.
  - 🥸 **Gentleman Mustache**: Classic handlebar mustache.
- **Smart QR Code & Barcode Scanner**:
  - Instant live decoding of QR codes and URLs.
  - 1-click **Copy Decoded Text** to clipboard.
  - 1-click **Open Link in Default Browser**.
- **Motion Detection & Security Guard**:
  - MOG2 background subtractor with real-time motion percentage meter and neon bounding boxes.
  - **Auto-Snapshot on Motion**: Automatically captures timestamped security photos when movement exceeds a customizable sensitivity threshold.

### 4. 🌐 Photo 3D Point Cloud Creation & Viewer Studio
- **Monocular 3D Reconstruction**:
  - Multi-cue depth estimation: Bilateral edge-preserving gradients + central focal weighting + facial convex dome priors.
  - Sub-50ms instant generation: Converts any webcam frame or photo into thousands of 3D coordinates $(X, Y, Z)$ with true RGB color mapping.
  - Automatic surface normal calculation $(N_x, N_y, N_z)$ and statistical outlier noise filtering.
- **Embedded Interactive 3D Canvas Studio**:
  - Vectorized NumPy 3D perspective projection running at **>100 FPS**.
  - **Interactive 3D Orbiting**: Left-click drag to orbit/rotate, Right-click drag to pan, Scroll wheel to zoom in/out.
  - **4 Real-Time 3D Shading Modes**:
    - `RGB Photo`: Full original photorealistic colors.
    - `Depth Heatmap`: Turbo depth spectrum visualization.
    - `Height Elevation`: Plasma vertical contour gradient.
    - `3D Lit`: Realistic virtual sunlight illumination with computed surface normals.
  - **Turntable Auto-Rotate**: Smooth 360° showcase spinning.
  - **Camera Presets**: Instant Front, Isometric, and Top view snapping.
- **Universal 3D Export & Inspection**:
  - Standard **`.PLY`** (Stanford Point Cloud) with RGB vertex colors and normals.
  - Standard **`.OBJ`** (Wavefront 3D Object) with vertex colors.
  - 1-Click **Launch in Windows 3D Viewer** (`os.startfile`).
  - 1-Click **Open in GPU-Accelerated Open3D Studio** (`o3d.visualization.draw_geometries`).

### 5. 🎬 Studio Recording & Capture
- **Synchronized MP4 Video Recording**:
  - Constant Frame Rate (CFR) `mp4v` encoder preventing fast-forward speed bugs.
  - **Pause & Resume** support during active recording (`P`).
  - Live recording HUD badge: Pulsing live recording dot, `REC 00:01:23`, and on-disk file size counter.
- **Self-Timer Photo Countdown**:
  - 3s, 5s, 10s countdowns with big glowing numerals centered on screen and procedural audio cues.
- **Burst Mode**: Rapid-fire capture of 3x, 5x, or 10x frames (`B`).
- **Time-Lapse Mode**: Automatic recurring capture at 1s, 2s, 5s, 10s, or 30s intervals saved into organized session folders.
- **SLR Shutter Flash & Procedural Sound**: Brief translucent white screen flash and mechanical shutter click sound (can be muted anytime).

### 6. 🖥️ Obsidian Studio UI & Media Gallery
- **Modern Obsidian Theme**: Deep dark theme with electric cyan, purple, and emerald neon accents.
- **Instant 2D/3D Viewport Switching**: Toggle between live camera preview and interactive 3D model studio anytime.
- **Framing Composition Guides (`G`)**:
  - Rule of Thirds
  - Center Crosshair & Reticle
  - Golden Ratio
- **Bottom Media Gallery Drawer**:
  - Lists recent photos and videos.
  - **Double-click** to open/play in default media player.
  - **Copy Image to Clipboard**: Direct Windows CF_DIB clipboard integration — paste directly into Discord, Slack, WhatsApp, Photoshop, or Word documents!
  - **Open Storage Folder**: Instant access in Windows Explorer.
- **Full Hotkey Navigation**: Total hands-on control for pro streaming.

---

## ⌨️ Pro Keyboard Shortcuts

| Shortcut | Action |
|:---|:---|
| <kbd>Space</kbd> | Take Photo / Start Countdown Timer |
| <kbd>R</kbd> | Start / Stop MP4 Video Recording |
| <kbd>P</kbd> | Pause / Resume Video Recording |
| <kbd>B</kbd> | Take Burst Snapshot (3x / 5x) |
| <kbd>M</kbd> | Toggle Selfie Mirror Mode |
| <kbd>G</kbd> | Cycle Framing Grids (None &rarr; Thirds &rarr; Crosshair &rarr; Golden) |
| <kbd>S</kbd> | Toggle Studio Audio Cues (Mute / Unmute) |
| <kbd>F11</kbd> | Toggle Fullscreen Mode |
| <kbd>Esc</kbd> | Exit Fullscreen Mode |

---

## 📦 Architecture Overview

```
web-cam-withgui/
├── engine/
│   ├── camera_stream.py      # DirectShow capture, resolution negotiation & synthetic fallback
│   ├── filter_engine.py      # 17 artistic filters, color grading, adjustments & digital zoom
│   ├── ai_vision.py          # Fast face tracking, EMA smoothing, AR props, QR scanner & motion guard
│   ├── point_cloud.py        # 3D Depth estimation, back-projection, normals & PLY/OBJ export
│   ├── recorder.py           # Synchronized MP4 video recorder, burst & time-lapse engine
│   └── audio_cue.py          # Procedural mechanical shutter sound & countdown beeps
├── ui/
│   ├── theme.py              # Studio Pro dark theme palette and TTK custom styles
│   ├── canvas_viewport.py    # Zero-flicker double-buffered canvas, framing grids & HUD
│   ├── point_cloud_viewer.py # Interactive 3D point cloud studio viewer (>100 FPS)
│   ├── gallery_panel.py      # Collapsible bottom media gallery drawer
│   └── clipboard_helper.py   # Windows native CF_DIB image & text clipboard copier
├── models/                   # Exported 3D Point Clouds (.PLY, .OBJ)
├── snapshots/                # Captured photos and time-lapse sessions
├── recordings/               # Recorded MP4 videos
├── tests/
│   ├── test_studio.py        # Core studio unit test suite
│   └── test_point_cloud.py   # 3D Point Cloud generator & export tests
├── main.py                   # Main Studio Application Entry Point
├── camera.py                 # Fully backward-compatible Camera API wrapper
├── build_exe.py              # Standalone executable build script (PyInstaller)
└── requirements.txt          # Project dependencies
```

---

## 🚀 Quickstart

### 1. Requirements
- Python 3.8+ (tested on Python 3.12)
- Windows 10/11, macOS, or Linux

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Launch Studio Application
```bash
python main.py
```

### 4. Run Test Suite
```bash
python -m unittest tests/test_studio.py
```

### 5. Build Standalone `.exe` (Optional)
```bash
python build_exe.py
```
The compiled executable will be placed in `./dist/WebcamStudioPro.exe`.

---

## 📄 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
