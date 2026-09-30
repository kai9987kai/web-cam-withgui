"""
build_exe.py - Build standalone Windows Executable using PyInstaller.
Run:
    python build_exe.py
"""

import os
import sys
import subprocess
import cv2

def build():
    print("=" * 60)
    print("Building Webcam Studio Pro Standalone Executable")
    print("=" * 60)

    # Locate OpenCV data folder
    cascade_dir = cv2.data.haarcascades
    add_data_arg = f"--add-data={cascade_dir};cv2/data"

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name=WebcamStudioPro",
        "--onefile",
        "--windowed",
        "--clean",
        add_data_arg,
        "--hidden-import=cv2",
        "--hidden-import=PIL",
        "--hidden-import=win32clipboard",
        "--hidden-import=pyperclip",
        "--hidden-import=open3d",
        "--hidden-import=plyfile",
        "main.py"
    ]

    print("Running command:", " ".join(cmd))
    result = subprocess.run(cmd)
    if result.returncode == 0:
        print("\n Build Successful! Executable located in ./dist/WebcamStudioPro.exe")
    else:
        print("\n Build failed with code:", result.returncode)

if __name__ == "__main__":
    build()
