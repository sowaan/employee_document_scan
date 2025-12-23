import os
import time
import shutil
import requests
import json
from datetime import datetime

#Set up paths and API details here 
# Configuration
SCAN_PATH = r"E:\Images"
TEMP_PATH = r"E:\Images\_temp"
ERP_SITE = "http://127.168.1.60:8000"

API_KEY = "XXXXXXXXX"
API_SECRET = "XXXXXXXXX"

HEADERS = {
    "Authorization": f"token {API_KEY}:{API_SECRET}"
}

os.makedirs(TEMP_PATH, exist_ok=True)


# Clean old temp images at startup
for file in os.listdir(TEMP_PATH):
    file_path = os.path.join(TEMP_PATH, file)
    if os.path.isfile(file_path):
        os.remove(file_path)
print(f"[{datetime.now()}] Old temp images deleted at startup.")


# Helper Functions
def upload_file(file_path):
    filename = os.path.basename(file_path)
    url = f"{ERP_SITE}/api/method/upload_file"

    with open(file_path, "rb") as f:
        files = {"file": (filename, f)}
        response = requests.post(url, headers=HEADERS, files=files, timeout=30)

    if response.status_code == 200:
        data = response.json()
        if data.get("message") and data["message"].get("file_url"):
            return data["message"]["file_url"]

    print(f"[{datetime.now()}] Upload failed: {response.text}")
    return None


def create_scanned_document(front_url, back_url):
    url = f"{ERP_SITE}/api/resource/Scanned Documents"

    payload = {"front_image": front_url, "back_image": back_url}

    response = requests.post(
        url,
        headers={**HEADERS, "Content-Type": "application/json"},
        data=json.dumps(payload),
        timeout=30
    )

    if response.status_code in (200, 201):
        print(f"[{datetime.now()}] Scanned Document created.")
        return True
    else:
        print(f"[{datetime.now()}] Failed to create document: {response.text}")
        return False


# Watcher
def watcher_loop():
    print(f"[{datetime.now()}] Watching ImageVis overwrite events...")

    image_path = os.path.join(SCAN_PATH, "ImageVis.png")

    # Initialize last_mtime to ignore the existing file at startup
    last_mtime = os.path.getmtime(image_path) if os.path.exists(image_path) else None

    front_copy = None
    back_copy = None

    while True:
        try:
            if os.path.exists(image_path):
                mtime = os.path.getmtime(image_path)

                # Only react if the file has been modified after script started
                if last_mtime is None or mtime != last_mtime:
                    last_mtime = mtime

                    # Copy to temp with timestamp
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                    temp_file = os.path.join(TEMP_PATH, f"ImageVis_{timestamp}.png")
                    shutil.copy2(image_path, temp_file)
                    print(f"[{datetime.now()}] Image captured")

                    # Decide if front or back
                    if front_copy is None:
                        front_copy = temp_file
                        print(f"[{datetime.now()}] Front side stored")
                    else:
                        back_copy = temp_file
                        print(f"[{datetime.now()}] Back side stored")

            # Only upload when BOTH sides are captured
            if front_copy and back_copy:
                front_url = upload_file(front_copy)
                back_url = upload_file(back_copy)

                if front_url and back_url:
                    if create_scanned_document(front_url, back_url):
                        # Remove temp copies after successful upload
                        os.remove(front_copy)
                        os.remove(back_copy)
                        print(f"[{datetime.now()}] Temp files deleted after upload")

                # Reset for next card
                front_copy = None
                back_copy = None

        except Exception as e:
            print(f"[{datetime.now()}] Error: {e}")

        time.sleep(1)


# Start
if __name__ == "__main__":
    watcher_loop()