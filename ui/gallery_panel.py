import os
import glob
import subprocess
import sys
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Callable
from PIL import Image, ImageTk
import cv2

from ui.clipboard_helper import ClipboardHelper


class GalleryPanel(ttk.Frame):
    """
    Interactive bottom media drawer:
    - Lists recent snapshots and video recordings
    - Thumbnail generation
    - 1-click 'Open in Explorer', 'Play/View', 'Copy to Clipboard', 'Delete'
    - Expandable / Collapsible
    """

    def __init__(self, parent, on_status_msg: Optional[Callable[[str], None]] = None, **kwargs):
        super().__init__(parent, style="Card.TFrame", **kwargs)
        self.on_status_msg = on_status_msg

        self.is_expanded = False
        self.recent_files = []
        self._thumbnail_cache = {}

        self._build_ui()
        self.refresh_gallery()

    def _build_ui(self):
        # Header bar / Toggle
        self.header_frame = ttk.Frame(self, style="CardLight.TFrame")
        self.header_frame.pack(fill=tk.X, padx=2, pady=2)

        self.btn_toggle = ttk.Button(self.header_frame, text="▲ MEDIA GALLERY (0)",
                                     style="Small.TButton", command=self.toggle_expanded)
        self.btn_toggle.pack(side=tk.LEFT, padx=6, pady=4)

        self.btn_refresh = ttk.Button(self.header_frame, text="🔄 Refresh",
                                      style="Small.TButton", command=self.refresh_gallery)
        self.btn_refresh.pack(side=tk.LEFT, padx=4, pady=4)

        self.btn_folder = ttk.Button(self.header_frame, text="📁 Open Folder",
                                     style="Small.TButton", command=self.open_storage_folder)
        self.btn_folder.pack(side=tk.LEFT, padx=4, pady=4)

        self.btn_copy = ttk.Button(self.header_frame, text="📋 Copy Selected",
                                   style="Small.TButton", command=self.copy_selected_to_clipboard)
        self.btn_copy.pack(side=tk.LEFT, padx=4, pady=4)

        self.btn_open = ttk.Button(self.header_frame, text="▶ Open File",
                                   style="Small.TButton", command=self.open_selected_file)
        self.btn_open.pack(side=tk.LEFT, padx=4, pady=4)

        self.btn_del = ttk.Button(self.header_frame, text="🗑 Delete",
                                  style="Small.TButton", command=self.delete_selected_file)
        self.btn_del.pack(side=tk.RIGHT, padx=6, pady=4)

        # Expandable drawer container
        self.drawer_container = ttk.Frame(self, style="Card.TFrame", height=110)

        # Scrollable horizontal canvas or listbox
        self.listbox_frame = ttk.Frame(self.drawer_container, style="Card.TFrame")
        self.listbox_frame.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        self.scrollbar = ttk.Scrollbar(self.listbox_frame, orient=tk.VERTICAL)
        self.media_listbox = tk.Listbox(self.listbox_frame, bg="#161824", fg="#F8FAFC",
                                        selectbackground="#00D2FF", selectforeground="#0A101D",
                                        font=("Segoe UI", 9), height=4, bd=0, highlightthickness=1,
                                        highlightcolor="#2B3048", yscrollcommand=self.scrollbar.set)
        self.scrollbar.config(command=self.media_listbox.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.media_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.media_listbox.bind("<Double-Button-1>", lambda e: self.open_selected_file())

    def toggle_expanded(self):
        """Toggle bottom gallery drawer open / closed."""
        self.is_expanded = not self.is_expanded
        if self.is_expanded:
            self.drawer_container.pack(fill=tk.X, expand=False, padx=2, pady=(0, 2))
            count = len(self.recent_files)
            self.btn_toggle.config(text=f"▼ HIDE GALLERY ({count})")
        else:
            self.drawer_container.pack_forget()
            count = len(self.recent_files)
            self.btn_toggle.config(text=f"▲ MEDIA GALLERY ({count})")

    def refresh_gallery(self):
        """Scan directories for recent photos and recordings."""
        files = []
        # Photos
        for ext in ("*.png", "*.jpg", "*.jpeg"):
            files.extend(glob.glob(os.path.join("snapshots", ext)))
            files.extend(glob.glob(os.path.join("snapshots", "**", ext), recursive=True))

        # Recordings
        for ext in ("*.mp4", "*.avi"):
            files.extend(glob.glob(os.path.join("recordings", ext)))

        # Sort newest first
        files.sort(key=lambda p: os.path.getmtime(p) if os.path.exists(p) else 0, reverse=True)
        self.recent_files = files[:60]

        # Update UI Listbox
        self.media_listbox.delete(0, tk.END)
        for f in self.recent_files:
            name = os.path.basename(f)
            size_kb = os.path.getsize(f) / 1024
            mtime = os.path.getmtime(f)
            time_str = cv2.getTickFrequency()  # dummy
            prefix = "📷 Photo: " if f.lower().endswith((".png", ".jpg", ".jpeg")) else "🎬 Video: "
            self.media_listbox.insert(tk.END, f"{prefix}{name}  ({size_kb:.0f} KB)")

        count = len(self.recent_files)
        arrow = "▼" if self.is_expanded else "▲"
        label = "HIDE" if self.is_expanded else "MEDIA"
        self.btn_toggle.config(text=f"{arrow} {label} GALLERY ({count})")

    def get_selected_path(self) -> Optional[str]:
        """Return the filepath of the selected listbox item."""
        sel = self.media_listbox.curselection()
        if sel and sel[0] < len(self.recent_files):
            return self.recent_files[sel[0]]
        elif self.recent_files:
            return self.recent_files[0]  # default to newest
        return None

    def open_storage_folder(self):
        """Open the snapshots/recordings storage folder in system file manager."""
        folder = os.path.abspath("snapshots")
        try:
            if sys.platform.startswith("win"):
                os.startfile(folder)
            elif sys.platform.startswith("darwin"):
                subprocess.Popen(["open", folder])
            else:
                subprocess.Popen(["xdg-open", folder])
            if self.on_status_msg:
                self.on_status_msg(f"Opened storage folder: {folder}")
        except Exception as e:
            messagebox.showerror("Error", f"Could not open folder: {e}")

    def open_selected_file(self):
        """Open selected file in default viewer/player."""
        path = self.get_selected_path()
        if not path or not os.path.exists(path):
            messagebox.showwarning("Notice", "No file selected.")
            return

        try:
            if sys.platform.startswith("win"):
                os.startfile(os.path.abspath(path))
            elif sys.platform.startswith("darwin"):
                subprocess.Popen(["open", os.path.abspath(path)])
            else:
                subprocess.Popen(["xdg-open", os.path.abspath(path)])
            if self.on_status_msg:
                self.on_status_msg(f"Opened: {os.path.basename(path)}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open file: {e}")

    def copy_selected_to_clipboard(self):
        """Copy selected image to Windows clipboard."""
        path = self.get_selected_path()
        if not path or not os.path.exists(path):
            messagebox.showwarning("Notice", "No file selected.")
            return

        if path.lower().endswith((".png", ".jpg", ".jpeg")):
            ok = ClipboardHelper.copy_image(path)
            if ok:
                if self.on_status_msg:
                    self.on_status_msg(f"Copied image to clipboard: {os.path.basename(path)}")
                return

        # Fallback copy file path
        ClipboardHelper.copy_text(os.path.abspath(path))
        if self.on_status_msg:
            self.on_status_msg(f"Copied path to clipboard: {os.path.basename(path)}")

    def delete_selected_file(self):
        """Delete selected item after confirmation."""
        path = self.get_selected_path()
        if not path or not os.path.exists(path):
            return

        filename = os.path.basename(path)
        confirm = messagebox.askyesno("Delete Media", f"Are you sure you want to permanently delete {filename}?")
        if confirm:
            try:
                os.remove(path)
                self.refresh_gallery()
                if self.on_status_msg:
                    self.on_status_msg(f"Deleted: {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Could not delete file: {e}")
