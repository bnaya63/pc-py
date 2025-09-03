import platform

system_type = platform.system()

if system_type == "Windows":
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
    from comtypes import CLSCTX_ALL


def get_volume():
    if system_type == "Windows":
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(
            IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = interface.QueryInterface(IAudioEndpointVolume)
        vol_now = int(volume.GetMasterVolumeLevelScalar() * 100)

        return vol_now

    elif system_type == "Linux":
        print("linux dose not support audio control yet")
        return None
    else:
        print("the system dose not support audio control")
        return None


def set_volume(var_set_volume):
    if system_type == "Windows":
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(
            IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = interface.QueryInterface(IAudioEndpointVolume)
        volume.SetMasterVolumeLevelScalar(var_set_volume / 100, None)
