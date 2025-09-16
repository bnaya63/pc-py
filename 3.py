import subprocess
import os
from PIL import Image


def extract_icons_from_exe(exe_path, out_dir="user_app_icons"):
    os.makedirs(out_dir, exist_ok=True)
    out_ico = os.path.join(out_dir, "temp.ico")

    # Run icoextract CLI
    subprocess.run([
        "icoextract.exe",
        exe_path,
        out_ico
    ], check=True)

    # Convert to PNG with PIL
    img = Image.open(out_ico).convert("RGBA")
    app_name = os.path.splitext(os.path.basename(exe_path))[0]
    out_path = os.path.join(out_dir, f"{app_name}.png")
    img.save(out_path, "PNG")

    os.remove(out_ico)
    print(f"Saved icon: {out_path}")
    return out_path


if __name__ == "__main__":
    test_exe = r"C:\Program Files\Microsoft VS Code\Code.exe"
    extract_icons_from_exe(test_exe)
