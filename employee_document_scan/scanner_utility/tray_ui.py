import pystray
from pystray import MenuItem as item
from PIL import Image, ImageDraw
import json
import os

CONTROL_FILE = "scanner_control.json"

def load_control():
    if not os.path.exists(CONTROL_FILE):
        return {"mode": "EID", "reset": False}
    with open(CONTROL_FILE) as f:
        return json.load(f)

def save_control(data):
    with open(CONTROL_FILE, "w") as f:
        json.dump(data, f)

def set_mode(mode):
    data = load_control()
    data["mode"] = mode
    save_control(data)

def reset_scan():
    data = load_control()
    data["reset"] = True
    save_control(data)

def create_icon():
    img = Image.new("RGB", (64, 64), "white")
    d = ImageDraw.Draw(img)
    d.rectangle((10, 10, 54, 54), outline="black", width=3)
    d.text((18, 22), "ID", fill="black")
    return img

def exit_app(icon, item):
    icon.stop()

def get_menu():
    data = load_control()
    mode = data.get("mode", "EID")
    
    return (
        item(
            "EID (2 sides)",
            lambda icon, item: set_mode("EID"),
            checked=lambda item: load_control().get("mode") == "EID"
        ),
        item(
            "PASSPORT (1 side)",
            lambda icon, item: set_mode("PASSPORT"),
            checked=lambda item: load_control().get("mode") == "PASSPORT"
        ),
        item(
            "Reset Current Scan",
            lambda icon, item: reset_scan()
        ),
        item("Exit", exit_app)
    )

def main():
    icon = pystray.Icon(
        "ScannerControl",
        create_icon(),
        "Scanner Control",
        menu=pystray.Menu(get_menu)  # just pass the function reference, no args
    )
    icon.run()

if __name__ == "__main__":
    main()
