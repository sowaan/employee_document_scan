import os
import subprocess
import sys
import time
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

tray_script = os.path.join(BASE_DIR, "tray_ui.py")
watcher_script = os.path.join(BASE_DIR, "watcher.py")

python_exe = sys.executable

python_dir = os.path.dirname(python_exe)
pythonw_exe = os.path.join(python_dir, "pythonw.exe")

if not os.path.exists(pythonw_exe):
    pythonw_exe = python_exe

watcher_log_path = os.path.join(BASE_DIR, "watcher_error.log")
tray_log_path = os.path.join(BASE_DIR, "tray_error.log")

print("Using Python:", python_exe)
print("Using PythonW:", pythonw_exe)
print("Tray script:", tray_script)
print("Watcher script:", watcher_script)
print("Watcher log:", watcher_log_path)
print("Tray log:", tray_log_path)

if not os.path.exists(tray_script):
    print("ERROR: tray_ui.py not found:", tray_script)
    sys.exit(1)

if not os.path.exists(watcher_script):
    print("ERROR: watcher.py not found:", watcher_script)
    sys.exit(1)

try:
    with open(watcher_log_path, "a", encoding="utf-8") as watcher_log, \
         open(tray_log_path, "a", encoding="utf-8") as tray_log:

        watcher_log.write("\n\n==============================\n")
        watcher_log.write(f"Watcher started at {datetime.now()}\n")
        watcher_log.write("==============================\n")
        watcher_log.flush()

        tray_log.write("\n\n==============================\n")
        tray_log.write(f"Tray started at {datetime.now()}\n")
        tray_log.write("==============================\n")
        tray_log.flush()

        if os.name == "nt":
            tray_process = subprocess.Popen(
                [pythonw_exe, tray_script],
                cwd=BASE_DIR,
                stdout=tray_log,
                stderr=tray_log
            )

            watcher_process = subprocess.Popen(
                [python_exe, watcher_script],
                cwd=BASE_DIR,
                stdout=watcher_log,
                stderr=watcher_log
            )
        else:
            tray_process = subprocess.Popen(
                [python_exe, tray_script],
                cwd=BASE_DIR,
                stdout=tray_log,
                stderr=tray_log
            )

            watcher_process = subprocess.Popen(
                [python_exe, watcher_script],
                cwd=BASE_DIR,
                stdout=watcher_log,
                stderr=watcher_log
            )

        print("Tray started. PID:", tray_process.pid)
        print("Watcher started. PID:", watcher_process.pid)

        while True:
            watcher_status = watcher_process.poll()
            tray_status = tray_process.poll()

            if watcher_status is not None:
                print("Watcher stopped with exit code:", watcher_status)
                print("Check watcher log:", watcher_log_path)
                sys.exit(1)

            if tray_status is not None:
                print("Tray stopped with exit code:", tray_status)
                print("Check tray log:", tray_log_path)
                sys.exit(1)

            time.sleep(5)

except Exception as e:
    print("Failed to start scanner processes:", str(e))
    sys.exit(1)