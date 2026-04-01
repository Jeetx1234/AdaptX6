import subprocess


def get_connected_devices():
    result = subprocess.check_output(["adb", "devices"]).decode()

    devices = []

    for line in result.split("\n")[1:]:
        if "device" in line:
            devices.append(line.split()[0])

    return devices
