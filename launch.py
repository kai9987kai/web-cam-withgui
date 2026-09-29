"""
launch.py - Launch Webcam Studio Pro onto the user's interactive Windows desktop.
"""

import os
import sys
import subprocess


def launch():
    cwd = os.path.dirname(os.path.abspath(__file__))
    log_path = os.path.join(cwd, "launch_error.log")
    try:
        import win32process
        si = win32process.STARTUPINFO()
        si.lpDesktop = r"WinSta0\Default"
        cmd = f'"{sys.executable}" "{os.path.join(cwd, "main.py")}"'
        with open(log_path, "w") as log_file:
            import win32con
            import win32file
            h_log = win32file.CreateFile(
                log_path, win32con.GENERIC_WRITE, win32con.FILE_SHARE_READ | win32con.FILE_SHARE_WRITE,
                None, win32con.CREATE_ALWAYS, 0, None
            )
            si.hStdOutput = h_log
            si.hStdError = h_log
            si.dwFlags |= win32process.STARTF_USESTDHANDLES
            hProcess, hThread, dwProcessId, dwThreadId = win32process.CreateProcess(
                None, cmd, None, None, True, 0, None, cwd, si
            )
        print(f"[Launcher] Successfully opened on interactive desktop WinSta0\\Default (PID: {dwProcessId})")
        return dwProcessId
    except Exception as e:
        print(f"[Launcher] Error in desktop launch: {e}")


if __name__ == "__main__":
    launch()
