import keyboard


# def get_active_window_name():
#    hwnd = win32gui.GetForegroundWindow()
#    return win32gui.GetWindowText(hwnd)


def send_cvx_command(command):

    match command:
        case "copy":
            keyboard.press_and_release("ctrl+c")
            print("copy")
        case "paste":
            keyboard.press_and_release("ctrl+v")
            print("paste")
        case "cut":
            keyboard.press_and_release("ctrl+x")
            print("cut")
        case _:
            print("default")
            return

    # if system_type == "Windows":
