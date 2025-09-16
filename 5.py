import os
import time
import psutil
import getpass
from PIL import Image
import subprocess
import win32gui
import win32process
import struct

# -----------------------------
# CONFIG
# -----------------------------
OUTPUT_FOLDER = "user_app_icons"
CHECK_INTERVAL = 1.0   # seconds

TEMP_ICON = "temp.ico"
ICON_PNG_FOLDER = "user_app_icons"
LVGL_BIN_FOLDER = "lvgl_bin_icons"
ICON_SIZE = (100, 100)  # width, height in px
LV_IMG_CF_TRUE_COLOR = 0x02  # RGB565

os.makedirs(ICON_PNG_FOLDER, exist_ok=True)
os.makedirs(LVGL_BIN_FOLDER, exist_ok=True)

# -----------------------------
# Functions
# -----------------------------


def extract_icon_from_exe(exe_path, output_png_folder=ICON_PNG_FOLDER):
    """
    Extract icon from EXE using icoextract.exe CLI and return a PIL.Image object.
    """
    app_name = os.path.splitext(os.path.basename(exe_path))[0]
    output_png = os.path.join(output_png_folder, f"{app_name}.png")

    try:
        # Run icoextract CLI -> outputs to temp.ico
        subprocess.run([
            "icoextract.exe",
            exe_path,
            TEMP_ICON
        ], check=True)

        # Load ICO into PIL
        img = Image.open(TEMP_ICON).convert("RGBA")

        # Save PNG for reference
        img.save(output_png, "PNG")
        os.remove(TEMP_ICON)

        print(f"Saved PNG icon: {output_png}")
        return img  # return PIL.Image
    except subprocess.CalledProcessError:
        print(f"Failed to extract icon from {exe_path}")
        return None
    except FileNotFoundError:
        print(f"{TEMP_ICON} not found, extraction failed")
        return None


def convert_png_to_lvgl_bin(img: Image.Image, app_name, output_folder=LVGL_BIN_FOLDER, size=ICON_SIZE):
    """
    Convert PIL.Image -> LVGL RGB565 .bin
    """
    img = img.convert("RGB").resize(size, Image.Resampling.LANCZOS)
    width, height = img.size
    pixels = list(img.getdata())

    # LVGL header: "LVGL" + width + height + color format
    header = b"LVGL" + struct.pack("<HHB", width, height, LV_IMG_CF_TRUE_COLOR)

    # Convert RGB888 -> RGB565
    pixel_data = bytearray()
    for r, g, b in pixels:
        rgb565 = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
        pixel_data += struct.pack("<H", rgb565)

    # Save bin file
    bin_path = os.path.join(output_folder, f"{app_name}.bin")
    with open(bin_path, "wb") as f:
        f.write(header)
        f.write(pixel_data)

    print(f"Saved LVGL .bin icon: {bin_path}")
    return bin_path


def enum_windows_pid_map():
    """
    Enumerate all visible windows and map them to PIDs.
    """
    pid_map = {}

    def _enum(hwnd, _):
        if not win32gui.IsWindowVisible(hwnd):
            return
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        pid_map.setdefault(pid, []).append(hwnd)

    win32gui.EnumWindows(_enum, None)
    return pid_map


def is_user_app(proc, window_pid_map, current_user=None):
    """
    Decide if a process is a "user app" (visible, owned by user, not system).
    """
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


# -----------------------------
# Main loop
# -----------------------------

def main():
    seen_pids = set()
    current_user = getpass.getuser()

    while True:
        window_pid_map = enum_windows_pid_map()
        for proc in psutil.process_iter(['pid', 'name', 'exe', 'username']):
            pid = proc.info['pid']
            if pid in seen_pids:
                continue
            if is_user_app(proc, window_pid_map, current_user=current_user):
                try:

                    raw_name = proc.info['name']
                    name = os.path.splitext(raw_name)[0]  # remove .exe
                    name = "".join(c for c in name if c.isalnum()
                                   or c in (" ", "_")).rstrip()

                    exe = proc.info['exe']
                    print("New user app:", pid, name, exe)

                    pil_icon = extract_icon_from_exe(exe)
                    if pil_icon:
                        convert_png_to_lvgl_bin(pil_icon, name)

                        # Also save PNG with PID for uniqueness
                        safe_name = "".join(
                            c for c in name if c.isalnum() or c in (" ", "_")
                        ).rstrip()
                        file_path = os.path.join(
                            OUTPUT_FOLDER, f"{safe_name}_{pid}.png"
                        )
                        pil_icon.save(file_path)
                        print(f"Saved icon: {file_path}")

                        seen_pids.add(pid)

                except Exception as e:
                    print("Error handling proc:", e)
        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
