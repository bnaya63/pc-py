import os
import time
import psutil
import getpass
import json
from datetime import datetime
from PIL import Image
import subprocess
import win32gui
import win32process
import struct
from main import board_is_connected


# -----------------------------
# CONFIG
# -----------------------------
OUTPUT_FOLDER = "user_app_icons"
CHECK_INTERVAL = 5   # seconds

TEMP_ICON = "temp.ico"
ICON_PNG_FOLDER = "user_app_icons"
LVGL_BIN_FOLDER = "lvgl_bin_icons"
HEIGHT = 100
WIDTH = 100  # width, height in px
LV_IMG_CF_TRUE_COLOR = 0x02  # RGB565
APPS_JSON = "apps.json"

os.makedirs(ICON_PNG_FOLDER, exist_ok=True)
os.makedirs(LVGL_BIN_FOLDER, exist_ok=True)

# -----------------------------
# Load / Save registry
# -----------------------------


def load_registry():
    if os.path.exists(APPS_JSON):
        with open(APPS_JSON, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_registry(registry):
    with open(APPS_JSON, "w", encoding="utf-8") as f:
        json.dump(registry, f, indent=2)

# -----------------------------
# Functions
# -----------------------------


def enum_windows_pid_map():
    pid_map = {}

    def _enum(hwnd, _):
        if not win32gui.IsWindowVisible(hwnd):
            return
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        pid_map.setdefault(pid, []).append(hwnd)
    win32gui.EnumWindows(_enum, None)
    return pid_map


def is_user_app(proc, window_pid_map, current_user=None):
    try:
        if current_user is None:
            current_user = getpass.getuser()
        username = proc.username()
        if not username or current_user.lower() not in username.lower():
            return False
        if proc.pid not in window_pid_map:
            return False
        exe = proc.exe()
        if not exe:
            return False
        exe_low = exe.lower()
        if r"windows" in exe_low:
            return False
        name = proc.name().lower()
        if name in ("svchost.exe", "services.exe", "lsass.exe", "winlogon.exe"):
            return False
        return True
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return False


def extract_icon_from_exe(exe_path, output_png_folder=ICON_PNG_FOLDER):
    """
    Extract icon from EXE using icoextract.exe CLI and return a PIL.Image object.
    """
    app_name = os.path.splitext(os.path.basename(exe_path))[0]
    output_png = os.path.join(output_png_folder, f"{app_name}.png")

    try:
        subprocess.run(["icoextract.exe", exe_path, TEMP_ICON], check=True)

        img = Image.open(TEMP_ICON).convert("RGBA")
        img.save(output_png, "PNG")
        os.remove(TEMP_ICON)

        print(f"Saved PNG icon: {output_png}")
        return img, output_png
    except Exception as e:
        print(f"Failed to extract icon from {exe_path}: {e}")
        return None, None


def convert_png_to_lvgl_bin(img: Image.Image, app_name, output_folder=LVGL_BIN_FOLDER, size=ICON_SIZE):
    """
    Convert PIL.Image -> LVGL RGB565 .bin
    """
    img = img.convert("RGB").resize(size, Image.Resampling.LANCZOS)
    width, height = img.size
    pixels = list(img.getdata())

    header = b"LVGL" + struct.pack("<HHB", width, height, LV_IMG_CF_TRUE_COLOR)

    pixel_data = bytearray()
    for r, g, b in pixels:
        rgb565 = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
        pixel_data += struct.pack("<H", rgb565)

    bin_path = os.path.join(output_folder, f"{app_name}.bin")
    with open(bin_path, "wb") as f:
        f.write(header)
        f.write(pixel_data)

    print(f"Saved LVGL .bin icon: {bin_path}")
    return bin_path


def calculate_scores(apps, alpha=1.0, beta=2.0):
    """Update registry with scores and return scored list."""
    now = datetime.now()
    scored_apps = []

    for app_name, data in apps.items():
        times_run = data.get("times_run", 0)
        last_run_str = data.get("last_run", None)

        # Default
        recency_score = 0
        if last_run_str:
            try:
                last_run = datetime.fromisoformat(last_run_str)
                days_since = (now - last_run).days
                if days_since < 1:
                    recency_score = 10
                elif days_since < 3:
                    recency_score = 5
                elif days_since < 7:
                    recency_score = 2
            except Exception:
                recency_score = 0

        score = (times_run * alpha) + (recency_score * beta)

        # 🔥 Store score in registry
        data["score"] = score
        apps[app_name] = data

        scored_apps.append((app_name, score))

    scored_apps.sort(key=lambda x: x[1], reverse=True)
    return scored_apps


def pick_top_apps(apps, limit=12):
    """Pick top apps based on score."""
    scored_apps = calculate_scores(apps)
    return [name for name, score in scored_apps[:limit]]


def app_icon_task():
    seen_pids = set()
    current_user = getpass.getuser()
    registry = load_registry()

    while True:
        window_pid_map = enum_windows_pid_map()
        for proc in psutil.process_iter(['pid', 'name', 'exe', 'username']):
            pid = proc.info['pid']
            if pid in seen_pids:
                continue
            if is_user_app(proc, window_pid_map, current_user=current_user):
                try:
                    raw_name = proc.info['name']
                    exe = proc.info['exe']
                    base_name = os.path.splitext(raw_name)[0]
                    safe_name = "".join(
                        c for c in base_name if c.isalnum() or c in (" ", "_")).rstrip()

                    print("New user app:", pid, raw_name, exe)

                    pil_icon, png_path = extract_icon_from_exe(exe)
                    if pil_icon:
                        bin_path = convert_png_to_lvgl_bin(pil_icon, safe_name)

                        # Save PID-specific copy for debugging
                        pid_png_path = os.path.join(
                            OUTPUT_FOLDER, f"{safe_name}_{pid}.png")
                        pil_icon.save(pid_png_path)
                        print(f"Saved icon: {pid_png_path}")

                        # Update registry
                        app_entry = registry.get(safe_name, {
                            "exe_path": exe,
                            "friendly_name": safe_name,
                            "icon_bin": bin_path,
                            "icon_png": png_path,
                            "times_run": 0,
                            "last_run": None
                        })
                        app_entry["times_run"] += 1
                        app_entry["last_run"] = datetime.now().isoformat()

                        registry[safe_name] = app_entry

                        # Recalculate scores & save
                        scored = calculate_scores(registry)
                        save_registry(registry)

                        # Pick top 12
                        top12 = [name for name, score in scored[:12]]
                        with open("top_apps.json", "w", encoding="utf-8") as f:
                            json.dump({"top12": top12}, f, indent=2)

                        save_registry(registry)

                        seen_pids.add(pid)
                except Exception as e:
                    print("Error handling proc:", e)
        time.sleep(CHECK_INTERVAL)


def send_icons_task():
    last_apps_list = load_registry()

    while board_is_connected.is_set():
        app_list = load_registry()

        # detect if new app(s) were added
        if len(app_list) > len(last_apps_list):
            # find new entries by set difference on keys
            new_keys = set(app_list.keys()) - set(last_apps_list.keys())

            for key in new_keys:
                new_entry = app_list[key]
                icon_path = new_entry["icon_bin"]
                icon = open(icon_path, 'rb')

                app_name = new_entry["friendly_name"]
                icon_bin_path = new_entry["icon_bin"]
                score = new_entry.get("score", 0)

                # send_to_esp32(message)

        # update last list for next loop
            last_apps_list = app_list

        time.sleep(1)  # avoid busy loop


# send this new entry to the ESP32
    message = {
        "new_app": "",
        "height": HEIGHT,
        "width": WIDTH,
        "crc": "",
        "score": ""

    }
