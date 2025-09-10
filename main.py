from serial_device import serial_handshake, find_serial_port, build_slow_message, build_fast_messege
import time
import json
from audio import set_volume
import screen_brightness_control as sbc
from copy_paste import send_cvx_command
import threading
import pythoncom

board_is_connected = threading.Event()

SERIAL_TIMEOUT = 5000
MAX_JSON_ERRORS = 15

# Choose the correct vid and pid of your board.
# On windows: Device Manager > device > Properties > Details > Hardware ID.
# On linux: lsusb


# uart bridge
# serial_chip_vid = 4292
# serial_chip_pid = 60000

# usb port
serial_chip_vid = 6790
serial_chip_pid = 29987

serial_lock = threading.Lock()


def slow_write_task(port):
    pythoncom.CoInitialize()
    while board_is_connected.is_set():

        messege = build_slow_message()
        with serial_lock:
            port.read_all()
            port.write((messege + "\n").encode("utf-8"))
            port.flush()
            time.sleep(0.5)


def fast_write_task(port):
    pythoncom.CoInitialize()
    while board_is_connected.is_set():
        messege = build_fast_messege()
        with serial_lock:
            port.read_all()
            port.write((messege + "\n").encode("utf-8"))
            port.flush()


def read_task(port):
    pythoncom.CoInitialize()

    while board_is_connected.is_set():
        if port.in_waiting > 0:
            data = port.read_until(b"\n").decode('utf-8').strip()
            if data:  # only process if not empty
                try:
                    data = json.loads(data)  # decode JSON

                    # print(data)

                    # --- handle parsed data ---
                    if isinstance(data, dict):  # only process dict JSON objects
                        if "command" in data:
                            var_set_command = data["command"]
                            if var_set_command:
                                send_cvx_command(var_set_command)
                        else:
                            var_set_volume = data.get("setVolume")
                            var_set_brightness = data.get("setBrightness")

                            if var_set_brightness is not None:
                                sbc.set_brightness(var_set_brightness)
                            if var_set_volume is not None:
                                set_volume(var_set_volume)
                    else:
                        print("Received non-dict JSON:", data)

                except json.JSONDecodeError:
                    print("Invalid JSON:", data)


def main():
    port = None

    while True:
        # Try to find and connect to device
        if port is None:
            port = find_serial_port(serial_chip_vid, serial_chip_pid)
            if port is None:
                print("Device not found, retrying...")
                time.sleep(0.7)
                continue

        # Perform handshake
        if port is not None:
            if serial_handshake(port):
                board_is_connected.set()
            else:
                print("Handshake failed")
                board_is_connected.clear()
                port.close()
                port = None
                continue

        if port is not None:
            t1 = threading.Thread(target=slow_write_task, args=(port,))
            t2 = threading.Thread(target=slow_write_task, args=(port,))
            t3 = threading.Thread(target=read_task, args=(port,))

            if board_is_connected.is_set():
                t1.start()
                t2.start()
                t3.start()

        while board_is_connected.is_set():
            time.sleep(1)

        board_is_connected.clear()

        port.close()
        port = None


if __name__ == "__main__":
    main()
