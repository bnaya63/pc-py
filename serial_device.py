from datetime import datetime
import time
import json
import socket
import platform

import serial
import serial.tools.list_ports

from audio import get_volume
from Systeminfo.system_Info import SystemInfo
import screen_brightness_control as sbc

import psutil      # for cpu/mem usage

system_info = SystemInfo()
info = system_info.get_all_info()


def find_serial_port(serial_chip_vid, serial_chip_pid):
    ports = serial.tools.list_ports.comports()
    for port in ports:
        if port.vid == serial_chip_vid and port.pid == serial_chip_pid:
            print(f"found esp32 on {port}")
            try:
                port_connected = serial.Serial(port.device, 230400, timeout=2)
                time.sleep(1)  # allow ESP32 reset after open
                return port_connected
            except Exception as e:
                print(f"Error: {e}")
                return None
    print("port not found")
    return None


def serial_handshake(port):
    if port is None:
        print("Handshake failed: Port is None")
        return False

    try:
        # Create JSON handshake message
        port.read_all()
        port.write(b"host_ok")
        port.flush()

        start = time.time()
        while time.time() - start < 2:  # 2 second timeout
            if port.in_waiting:
                data = port.read_all()
                print(f"Received raw data: {data}")

                if b"ESP32_ok" in data:
                    print("Handshake successful (raw)")
                    return True
            time.sleep(0.01)

    except Exception as e:
        print(f"Handshake error: {e}")

    print("Handshake timed out")
    return False


# ------------ Helper functions ------------


def is_internet_reachable(timeout=1.0) -> bool:
    try:
        s = socket.create_connection(("8.8.8.8", 53), timeout=timeout)
        s.close()
        return True
    except OSError:
        return False


def classify_iface(name: str) -> str:
    n = name.lower()
    if "wi-fi" in n or "wifi" in n or "wlan" in n:
        return "wifi"
    if "ethernet" in n or "eth" in n or n.startswith("en"):
        return "ethernet"
    if n == "lo" or "loopback" in n:
        return "loopback"
    return "other"


def iface_ipv4(name: str) -> str:
    addrs = psutil.net_if_addrs().get(name, [])
    for snic in addrs:
        if snic.family == socket.AF_INET:
            return snic.address
    return ""


def network_snapshot():
    stats = psutil.net_if_stats()
    result = []
    for iface, st in stats.items():
        kind = classify_iface(iface)
        # skip loopback and "other"
        if kind in ("loopback", "other"):
            continue
        result.append({
            "name": iface,
            "kind": classify_iface(iface),
            "up": bool(st.isup),
            "ip": iface_ipv4(iface),
        })
    return result


def get_cpu_temp():
    """Try to get CPU temperature (Linux only)."""
    try:
        temps = psutil.sensors_temperatures()
        if "coretemp" in temps:
            return int(temps["coretemp"][0].current)
        elif temps:
            # Pick the first available sensor
            first = list(temps.values())[0]
            return int(first[0].current)
    except:
        pass
    return 0


def get_date_time():
    now = datetime.now()

    # Format as strings
    current_date = now.strftime("%d-%m-%y")   # e.g. "2025-08-22"
    current_time = now.strftime("%H:%M:%S")   # e.g. "18:47:12"
    return current_date, current_time

# ------------ Build message ------------


def build_slow_message():
    current_date, current_time = get_date_time()
    battery = psutil.sensors_battery()
    msg = {
        # String values
        "OSName": platform.system(),
        "time": current_time,
        "date": current_date,

        # Int values
        "cpuUsage": int(psutil.cpu_percent()),
        "cpuTemp": get_cpu_temp(),
        "memMax": int(psutil.virtual_memory().total / (1024*1024)),   # MB
        "MemUsage": int(psutil.virtual_memory().used / (1024*1024)),  # MB

        "batteryPercent": battery.percent,
        "powerIn": battery.power_plugged,
        # "internet": is_internet_reachable(),
        # "interfaces": network_snapshot()
    }
    return json.dumps(msg)


def build_fast_messege():
    msg = {
        "volume": get_volume(),
        "brightness": int(sbc.get_brightness(display=0)[0]),
    }
    return json.dumps(msg)
