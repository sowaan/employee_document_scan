import os
import time
import shutil
import requests
import json
import sys
import traceback
from datetime import datetime

# ================= CONFIG =================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# SCAN_PATH = r"E:\Images"            # old (E: drive not present on scanner PC)
# TEMP_PATH = r"E:\Images\_temp"
SCAN_PATH = r"C:\Users\shama\Documents\Picture"        # matches OutputWedge "Combined Data" dest
TEMP_PATH = r"C:\Users\shama\Documents\Picture\_temp"

# ERP_SITE = "http://192.168.43.82:8000"   # No trailing slash (old local/dev)
ERP_SITE = "https://daralburaq.sowaanerp.com"   # No trailing slash (production)

ERP_USERNAME = "shayan.rahim@sowaan.com"
ERP_PASSWORD = "Shayan_2255"

CONTROL_FILE = os.path.join(BASE_DIR, "scanner_control.json")

# ================= SESSION =================
session = requests.Session()


# ================= LOGGING =================
def log(*args):
    print(f"[{datetime.now()}]", *args, flush=True)


def log_exception(title, e):
    log(title, str(e))
    traceback.print_exc()


# ================= STARTUP CHECKS =================
def ensure_folders():
    if not os.path.exists(SCAN_PATH):
        log("ERROR: Scan path does not exist:", SCAN_PATH)
        log("Please confirm scanner output folder is correct.")
        return False

    try:
        os.makedirs(TEMP_PATH, exist_ok=True)
    except Exception as e:
        log_exception("ERROR: Could not create temp folder:", e)
        return False

    return True


def cleanup_temp_folder():
    try:
        for f in os.listdir(TEMP_PATH):
            fp = os.path.join(TEMP_PATH, f)
            if os.path.isfile(fp):
                os.remove(fp)

        log("Temp folder cleaned.")
    except Exception as e:
        log_exception("Temp folder cleanup failed:", e)


# ================= LOGIN =================
def erp_login():
    session.cookies.clear()
    session.headers.clear()

    login_url = f"{ERP_SITE}/api/method/login"

    try:
        response = session.post(
            login_url,
            data={"usr": ERP_USERNAME, "pwd": ERP_PASSWORD},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=15
        )

        try:
            resp_json = response.json()
        except Exception:
            log("ERP login returned non-JSON response:", response.text)
            return False

        if response.status_code == 200 and resp_json.get("message") == "Logged In":
            csrf_token = session.cookies.get("csrf_token")

            if csrf_token:
                session.headers.update({
                    "X-Frappe-CSRF-Token": csrf_token
                })

            log("ERP login successful")
            return True

        log("ERP login failed:", resp_json)
        return False

    except Exception as e:
        log_exception("ERP login error:", e)
        return False


def wait_until_erp_login():
    while True:
        if erp_login():
            return True

        log("ERP login failed. Retrying in 10 seconds...")
        time.sleep(10)


# ================= CONTROL FILE =================
def read_control():
    default_control = {"mode": "EID", "reset": False}

    try:
        if not os.path.exists(CONTROL_FILE):
            write_control(default_control)
            return default_control

        with open(CONTROL_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    except Exception as e:
        log_exception("Control file read failed:", e)
        return default_control


def write_control(data):
    try:
        with open(CONTROL_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f)
    except Exception as e:
        log_exception("Control file write failed:", e)


# ================= HELPERS =================
def upload_file(file_path):
    url = f"{ERP_SITE}/api/method/upload_file"

    try:
        with open(file_path, "rb") as f:
            files = {
                "file": (os.path.basename(file_path), f, "image/png")
            }

            r = session.post(
                url,
                files=files,
                timeout=30
            )

        if r.status_code == 200:
            file_url = r.json().get("message", {}).get("file_url")
            log("File uploaded:", file_url)
            return file_url

        log("Upload failed:", r.status_code, r.text)
        return None

    except Exception as e:
        log_exception("Upload error:", e)
        return None


def create_scanned_document(front_url, back_url=None, is_single=0):
    url = f"{ERP_SITE}/api/resource/Scanned Documents"

    payload = {
        "front_image": front_url,
        "is_single": is_single
    }

    if back_url:
        payload["back_image"] = back_url

    try:
        r = session.post(
            url,
            json=payload,
            timeout=30
        )

        if r.status_code in (200, 201):
            log(f"Scanned Document created successfully. is_single={is_single}")
            return True

        log("Document creation failed:", r.status_code, r.text)
        return False

    except Exception as e:
        log_exception("Error creating document:", e)
        return False


def safe_remove(file_path):
    try:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        log_exception("File remove failed:", e)


# ================= WATCHER =================
def watcher_loop():
    image_path = os.path.join(SCAN_PATH, "ImageVis.png")
    last_mtime = os.path.getmtime(image_path) if os.path.exists(image_path) else None

    front_copy = None
    back_copy = None

    log("Watching scanner...")
    log("Scanner image path:", image_path)
    log("Control file:", CONTROL_FILE)

    while True:
        try:
            control = read_control()
            mode = control.get("mode", "EID")

            # -------- RESET FROM UI --------
            if control.get("reset"):
                log("Reset requested from UI")

                safe_remove(front_copy)
                safe_remove(back_copy)

                front_copy = None
                back_copy = None

                control["reset"] = False
                write_control(control)

            # -------- SCAN DETECTION --------
            if os.path.exists(image_path):
                mtime = os.path.getmtime(image_path)

                if last_mtime is None or mtime != last_mtime:
                    last_mtime = mtime

                    # small delay so scanner finishes writing image
                    time.sleep(0.5)

                    ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                    temp_file = os.path.join(TEMP_PATH, f"scan_{ts}.png")

                    shutil.copy2(image_path, temp_file)
                    log("Image captured:", temp_file)

                    if not front_copy:
                        front_copy = temp_file
                        log("Front captured")
                    else:
                        back_copy = temp_file
                        log("Back captured")

            else:
                log("Waiting for scanner image file:", image_path)
                time.sleep(3)

            # -------- PASSPORT MODE / 1 SIDE --------
            if mode == "PASSPORT" and front_copy:
                front_url = upload_file(front_copy)

                if front_url and create_scanned_document(front_url, is_single=1):
                    safe_remove(front_copy)
                    log("Passport uploaded")

                front_copy = None
                back_copy = None

            # -------- EID MODE / 2 SIDES --------
            if mode == "EID" and front_copy and back_copy:
                front_url = upload_file(front_copy)
                back_url = upload_file(back_copy)

                if front_url and back_url and create_scanned_document(
                    front_url,
                    back_url,
                    is_single=0
                ):
                    safe_remove(front_copy)
                    safe_remove(back_copy)
                    log("EID uploaded")

                front_copy = None
                back_copy = None

        except Exception as e:
            log_exception("Watcher loop error:", e)

        time.sleep(1)


# ================= START =================
if __name__ == "__main__":
    try:
        log("Watcher starting...")

        if not ensure_folders():
            log("Folder check failed. Keeping watcher alive. Retrying every 10 seconds...")

            while not ensure_folders():
                time.sleep(10)

        cleanup_temp_folder()

        wait_until_erp_login()
        watcher_loop()

    except Exception as e:
        log_exception("Fatal watcher error:", e)
        sys.exit(1)