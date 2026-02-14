# web-cam-withgui (Webcam Pro – Advanced Capture)

A desktop webcam application with a modern Tkinter GUI and an OpenCV capture pipeline. It supports multi-camera selection, live filters, optional face tracking overlays, snapshots, and video recording.

Repo contains:
- `main.py` (Tkinter GUI application) :contentReference[oaicite:0]{index=0}
- `camera.py` (OpenCV capture/processing/recording backend running in a background thread) :contentReference[oaicite:1]{index=1}

---

## Features

- **Live preview** rendered into a resizable Tkinter canvas :contentReference[oaicite:2]{index=2}
- **Camera discovery** (index scan) and **device switching** from the GUI :contentReference[oaicite:3]{index=3}
- **Filters**:
  - Normal
  - Grayscale
  - Sepia
  - Edges (Canny)
  - Cartoon (adaptive threshold + bilateral filter)
  - Blur (Gaussian) :contentReference[oaicite:4]{index=4}
- **Face tracking overlay** (Haar cascade bounding boxes) :contentReference[oaicite:5]{index=5}
- **Snapshots** saved to `./snapshots/` with timestamped filenames :contentReference[oaicite:6]{index=6}
- **Video recording** saved to `./recordings/` as `.avi` (XVID) :contentReference[oaicite:7]{index=7}

---

## Requirements

- Python 3.x
- A working webcam (or capture device)
- Packages:
  - `opencv-python`
  - `Pillow`

> Notes:
> - The app uses OpenCV’s `VideoCapture(index)` scanning indices `0..max_search-1` (default `max_search=5`). :contentReference[oaicite:8]{index=8}  
> - Recording uses `cv2.VideoWriter` with XVID into AVI. Some systems may require codec support (see Troubleshooting). :contentReference[oaicite:9]{index=9}

---

## Install

Clone:

```bash
git clone https://github.com/kai9987kai/web-cam-withgui.git
cd web-cam-withgui
