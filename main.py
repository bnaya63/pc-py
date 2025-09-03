from serial_device import serial_handshake, find_serial_port, build_message
import time
import json
from audio import set_volume
import screen_brightness_control as sbc

SERIAL_TIMEOUT = 5000

# Choose the correct vid and pid of your board.
# On windows: Device Manager > device > Properties > Details > Hardware ID.
# On linux: lsusb


# uart bridge
# serial_chip_vid = 4292
# serial_chip_pid = 60000

# usb port
serial_chip_vid = 6790
serial_chip_pid = 29987


def main():
    port = None
    last_receive_time = 0

    while True:
        # Try to find and connect to device
        if port is None:
            port = find_serial_port(serial_chip_vid, serial_chip_pid)
            if port is None:
                print("Device not found, retrying...")
                time.sleep(0.7)
                continue

        # Perform handshake
        if not serial_handshake(port):
            print("Handshake failed")
            port.close()
            port = None
            continue

        # Main operation loop
        try:
            while True:
                # send messege
                messege = build_message()
                print(messege)
                port.read_all()
                port.write((messege + "\n").encode("utf-8"))
                port.flush()

                # recive messege
                if port.in_waiting > 0:  # if data is available
                    line = port.read_until(b"\n").decode('utf-8').rstrip()
                    if line:  # only process if not empty
                        try:
                            data = json.loads(line)  # decode JSON
                            var_set_volume = data.get("setVolume")
                            var_set_brightness = data.get("setBrightness")

                            if var_set_brightness is not None:
                                sbc.set_brightness(var_set_brightness)

                            if var_set_volume is not None:
                                set_volume(var_set_volume)

                            last_receive_time = int(time.time() * 1000)
                            time.sleep(0.2)

                        except json.JSONDecodeError:
                            print("Invalid JSON:", line)
                else:
                    now = int(time.time() * 1000)
                    if last_receive_time != 0 and (now - last_receive_time >= SERIAL_TIMEOUT):
                        print("⚠️ Serial timeout — no data received.")
                        last_receive_time = 0
                        break

        except Exception as e:
            print(f"Error in main loop: {e}")
            # port.close()
            # port = None


if __name__ == "__main__":
    main()
