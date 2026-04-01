import subprocess


class PhoneServer:

    def __init__(self, device_id):
        self.device_id = device_id
        self.state = "ON"

    def run_cmd(self, cmd):
        result = subprocess.check_output(
            ["adb", "-s", self.device_id] + cmd
        ).decode()
        return result

    def get_temperature(self):
        output = self.run_cmd(["shell", "dumpsys", "battery"])

        for line in output.split("\n"):
            if "temperature" in line:
                temp = int(line.split(":")[1].strip()) / 10
                return temp

        return None

    def get_battery(self):
        output = self.run_cmd(["shell", "dumpsys", "battery"])

        for line in output.split("\n"):
            if "level" in line:
                return int(line.split(":")[1].strip())

        return None

    def screen_off(self):
        self.run_cmd(["shell", "input", "keyevent", "26"])
        self.state = "OFF"

    def screen_on(self):
        self.run_cmd(["shell", "input", "keyevent", "26"])
        self.state = "ON"
