import os
import subprocess
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

tray_script = os.path.join(BASE_DIR, "tray_ui.py")
watcher_script = os.path.join(BASE_DIR, "watcher.py")

python_exe = sys.executable           # full path to python.exe
pythonw_exe = python_exe.replace("python.exe", "pythonw.exe")

if os.name == "nt":
    # Start tray (no console)
    subprocess.Popen(
        f'start "" "{pythonw_exe}" "{tray_script}"',
        shell=True
    )

    # Start watcher (with console for logs)
    subprocess.Popen(
        f'start "" "{python_exe}" "{watcher_script}"',
        shell=True
    )
else:
    subprocess.Popen([python_exe, tray_script])
    subprocess.Popen([python_exe, watcher_script])
