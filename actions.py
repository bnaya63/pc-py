import keyboard
import subprocess

# def get_active_window_name():
#    hwnd = win32gui.GetForegroundWindow()
#    return win32gui.GetWindowText(hwnd)


apps = {
    "vivaldi": "C:\\Users\\bnaya\\AppData\\Local\\Vivaldi\\Application\\vivaldi.exe",
    "Code": "C:\\Program Files\\Microsoft VS Code\\Code.exe",
    "EEZ Studio": "C:\\Users\\bnaya\\AppData\\Local\\Programs\\eezstudio\\EEZ Studio.exe",
    "wps": "C:\\Users\\bnaya\\AppData\\Local\\Kingsoft\\WPS Office\\12.2.0.22222\\office6\\wps.exe",
    "copyq": "C:\\Program Files\\CopyQ\\copyq.exe",
    "Listary": "C:\\Program Files\\Listary\\Listary.exe",
    "putty": "C:\\Program Files\\PuTTY\\putty.exe",
    "HxD": "C:\\Program Files\\HxD\\HxD.exe",
    "freecad": "C:\\Program Files\\FreeCAD 1.0\\bin\\freecad.exe",
    "Wireshark": "C:\\Program Files\\Wireshark\\Wireshark.exe",
    "7zFM": "C:\\Program Files\\7-Zip\\7zFM.exe",
    "nw": "C:\\Program Files (x86)\\Open Source\\MeshCommander\\nw.exe",
    "prusaslicer": "C:\\Program Files\\Prusa3D\\PrusaSlicer\\prusa-slicer.exe",
    "balenaEtcher": "C:\\Users\\bnaya\\AppData\\Local\\balena_etcher\\app-2.1.0\\balenaEtcher.exe",
    "Brother iPrintScan": "C:\\Program Files (x86)\\Brother\\iPrint&Scan\\Brother iPrint&Scan.exe",
    "HWMonitor": "C:\\Program Files\\CPUID\\HWMonitor\\HWMonitor.exe",
    "obs64": "C:\\Program Files\\obs-studio\\bin\\64bit\\obs64.exe",
    "Telegram": "C:\\Users\\bnaya\\AppData\\Roaming\\Telegram Desktop\\Telegram.exe",
    "VirtualBox": "C:\\Program Files\\Oracle\\VirtualBox\\VirtualBox.exe",
    "vlc": "C:\\Program Files\\VideoLAN\\VLC\\vlc.exe",
    "Zoom": "C:\\Users\\bnaya\\AppData\\Roaming\\Zoom\\bin\\Zoom.exe",
    "fdm": "C:\\Program Files\\Softdeluxe\\Free Download Manager\\fdm.exe"
}


DETACHED_PROCESS = 0x00000008
CREATE_NEW_CONSOLE = 0x00000010


def launch_app(key: str):
    exe_path = apps.get(key)
    if not exe_path:
        print(f"Unknown app: {key}")
        return

    try:
        # Launch as independent user process
        subprocess.Popen(exe_path, close_fds=True)
        print(f"Launched {key} as independent process")
    except Exception as e:
        print(f"Failed to launch {key}: {e}")


def do_action(command):
    match command:
        # copy paste actions
        case "copy":
            keyboard.press_and_release("ctrl+c")
            print("copy")
        case "paste":
            keyboard.press_and_release("ctrl+v")
            print("paste")
        case "cut":
            keyboard.press_and_release("ctrl+c")
            print("cut")

       # launch app actions
    match command:
        case "vivaldi":
            launch_app("vivaldi")
        case "code":
            launch_app("Code")
        case "eez_studio":
            launch_app("EEZ Studio")
        case "wps":
            launch_app("wps")
        case "copyq":
            launch_app("copyq")
        case "listary":
            launch_app("Listary")
        case "putty":
            launch_app("putty")
        case "hx_d":
            launch_app("HxD")
        case "freecad":
            launch_app("freecad")
        case "wireshark":
            launch_app("Wireshark")
        case "sevenz_fm":
            launch_app("7zFM")
        case "mesh_commander":
            launch_app("nw")
        case "prusa_slicer":
            launch_app("prusaslicer")
        case "balena_etcher":
            launch_app("balenaEtcher")
        case "brother_i_print_scan":
            launch_app("Brother iPrintScan")
        case "hw_monitor":
            launch_app("HWMonitor")
        case "obs":
            launch_app("obs64")
        case "telegram":
            launch_app("Telegram")
        case "virtual_box":
            launch_app("VirtualBox")
        case "vlc":
            launch_app("vlc")
        case "zoom":
            launch_app("Zoom")
        case _:
            print(f"⚠️ No matching app for command: {command}")
