import os
import subprocess
from PIL import Image
import struct

# -----------------------------
# Config
# -----------------------------
EXE_LIST = [
    r"C:\Program Files\Microsoft VS Code\Code.exe",
    r"C:\Users\bnaya\AppData\Local\Programs\eezstudio\EEZ Studio.exe",
    r"C:\Users\bnaya\AppData\Local\Vivaldi\Application\vivaldi.exe"
]

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
    Extract icon from EXE using icoextract.exe CLI
    """
    app_name = os.path.splitext(os.path.basename(exe_path))[0]
    output_png = os.path.join(output_png_folder, f"{app_name}.png")

    # Run icoextract CLI
    try:
        subprocess.run([
            "icoextract.exe",
            exe_path,
            TEMP_ICON
        ], check=True)

        # Convert temp.ico -> PNG
        img = Image.open(TEMP_ICON).convert("RGBA")
        img.save(output_png, "PNG")
        os.remove(TEMP_ICON)
        print(f"Saved PNG icon: {output_png}")
        return output_png
    except subprocess.CalledProcessError:
        print(f"Failed to extract icon from {exe_path}")
        return None
    except FileNotFoundError:
        print(f"{TEMP_ICON} not found, extraction failed")
        return None


def convert_png_to_lvgl_bin(png_path, output_folder=LVGL_BIN_FOLDER, size=ICON_SIZE):
    """
    Convert PNG -> LVGL RGB565 .bin
    """
    img = Image.open(png_path).convert("RGB")
    img = img.resize(size, Image.Resampling.LANCZOS)
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
    app_name = os.path.splitext(os.path.basename(png_path))[0]
    bin_path = os.path.join(output_folder, f"{app_name}.bin")
    with open(bin_path, "wb") as f:
        f.write(header)
        f.write(pixel_data)

    print(f"Saved LVGL .bin icon: {bin_path}")
    return bin_path


# -----------------------------
# Main
# -----------------------------
if __name__ == "__main__":
    for exe in EXE_LIST:
        png_icon = extract_icon_from_exe(exe)
        if png_icon:
            convert_png_to_lvgl_bin(png_icon)
