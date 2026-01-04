import os
import time
import shutil
import requests
import json
from datetime import datetime

# ================= CONFIG =================
SCAN_PATH = r"E:\Images"
TEMP_PATH = r"E:\Images\_temp"
ERP_SITE = "http://192.168.43.82:8000"   # No trailing slash

ERP_USERNAME = "Administrator"
ERP_PASSWORD = "root"

CONTROL_FILE = "scanner_control.json"

os.makedirs(TEMP_PATH, exist_ok=True)

# ================= SESSION =================
session = requests.Session()

# ================= STARTUP CLEANUP =================
for f in os.listdir(TEMP_PATH):
    fp = os.path.join(TEMP_PATH, f)
    if os.path.isfile(fp):
        os.remove(fp)
print(f"[{datetime.now()}] Temp folder cleaned.")

#==================Login======================
def erp_login():
    session.cookies.clear()
    login_url = f"{ERP_SITE}/api/method/login"

    try:
        response = session.post(
            login_url,
            data={"usr": ERP_USERNAME, "pwd": ERP_PASSWORD},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=15
        )

        resp_json = response.json()
        if response.status_code == 200 and resp_json.get("message") == "Logged In":
            csrf_token = session.cookies.get("csrf_token")
            if csrf_token:
                session.headers.update({
                    "X-Frappe-CSRF-Token": csrf_token,
                    "Content-Type": "application/json"
                })
            print(f"[{datetime.now()}] ERP login successful")
            return True
        else:
            print(f"[{datetime.now()}] ERP login failed:", resp_json)
            return False

    except Exception as e:
        print(f"[{datetime.now()}] ERP login error:", e)
        return False


# ================= CONTROL FILE =================
def read_control():
    try:
        with open(CONTROL_FILE) as f:
            return json.load(f)
    except:
        return {"mode": "EID", "reset": False}

def write_control(data):
    with open(CONTROL_FILE, "w") as f:
        json.dump(data, f)

# ================= HELPERS =================
def upload_file(file_path):
    url = f"{ERP_SITE}/api/method/upload_file"
    with open(file_path, "rb") as f:
        files = {"file": (os.path.basename(file_path), f)}
        r = session.post(url, files=files, timeout=30)
    if r.status_code == 200:
        return r.json().get("message", {}).get("file_url")
    print(f"[{datetime.now()}] Upload failed:", r.text)
    return None


# 🔹 FIXED: added is_single
def create_scanned_document(front_url, back_url=None, is_single=0):
    url = f"{ERP_SITE}/api/resource/Scanned Documents"

    payload = {
        "front_image": front_url,
        "is_single": is_single
    }

    if back_url:
        payload["back_image"] = back_url

    try:
        r = session.post(url, data=json.dumps(payload), timeout=30)
        if r.status_code in (200, 201):
            print(f"[{datetime.now()}] Scanned Document created (is_single={is_single})")
            return True
        print(f"[{datetime.now()}] Document creation failed:", r.text)
        return False
    except Exception as e:
        print(f"[{datetime.now()}] Error creating document:", e)
        return False


# ================= WATCHER =================
def watcher_loop():
    image_path = os.path.join(SCAN_PATH, "ImageVis.png")
    last_mtime = os.path.getmtime(image_path) if os.path.exists(image_path) else None

    front_copy = None
    back_copy = None

    print(f"[{datetime.now()}] Watching scanner...")

    while True:
        try:
            control = read_control()
            MODE = control.get("mode", "EID")

            # -------- RESET FROM UI --------
            if control.get("reset"):
                print(f"[{datetime.now()}] Reset requested from UI")
                if front_copy and os.path.exists(front_copy):
                    os.remove(front_copy)
                if back_copy and os.path.exists(back_copy):
                    os.remove(back_copy)
                front_copy = None
                back_copy = None
                control["reset"] = False
                write_control(control)

            # -------- SCAN DETECTION --------
            if os.path.exists(image_path):
                mtime = os.path.getmtime(image_path)
                if last_mtime is None or mtime != last_mtime:
                    last_mtime = mtime
                    ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                    temp_file = os.path.join(TEMP_PATH, f"scan_{ts}.png")
                    shutil.copy2(image_path, temp_file)
                    print(f"[{datetime.now()}] Image captured")

                    if not front_copy:
                        front_copy = temp_file
                        print(f"[{datetime.now()}] Front captured")
                    else:
                        back_copy = temp_file
                        print(f"[{datetime.now()}] Back captured")

            # -------- PASSPORT MODE (1 SIDE) --------
            if MODE == "PASSPORT" and front_copy:
                front_url = upload_file(front_copy)
                if front_url and create_scanned_document(
                    front_url,
                    is_single=1
                ):
                    os.remove(front_copy)
                    print(f"[{datetime.now()}] Passport uploaded")
                front_copy = None
                back_copy = None

            # -------- EID MODE (2 SIDES) --------
            if MODE == "EID" and front_copy and back_copy:
                front_url = upload_file(front_copy)
                back_url = upload_file(back_copy)
                if front_url and back_url and create_scanned_document(
                    front_url,
                    back_url,
                    is_single=0
                ):
                    os.remove(front_copy)
                    os.remove(back_copy)
                    print(f"[{datetime.now()}] EID uploaded")
                front_copy = None
                back_copy = None

        except Exception as e:
            print(f"[{datetime.now()}] Error:", e)

        time.sleep(1)

# ================= START =================
if __name__ == "__main__":
    if erp_login():
        watcher_loop()
    else:
        print(f"[{datetime.now()}] Exiting: ERP login failed")
