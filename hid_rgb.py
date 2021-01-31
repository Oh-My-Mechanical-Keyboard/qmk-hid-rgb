
"""
Possible message format:
    0x01: Sets the LED state
        0x01: All LEDs on
        0x02: Keylight only
        0x03: Underglow only
        0x04: All LEDs off
        0x05: Next RGB animation
    0x02: Notifications
        0x01: Set the "bottom" (user-facing) part of the underglow to a specific color
            0xXX: Red value
            0xXX: Green value
            0xXX: Blue value
        0x02: Set the whole keyboard to a color
            (same RGB parameters)
        0x03: Set the whole underglow to a color
            (same RGB parameters)
    0x03: Get the current LED state
        No parameters, returns (sends) a value as in the 0x01 section
"""

import hid
from time import sleep

# NOTE: Change the 64 here if your board uses 32-byte RAW_EPSIZE
def pad_message(payload):
    return payload + b'\x00' * (64 - len(payload))

def tobyte(data):
    if type(data) is bytes:
        return data
    else:
        return (data).to_bytes(1, 'big')

def tobytes(data):
    out = b''
    for num in data:
        out += tobyte(num)
    return out
class Alt:

    device = None
    name2bytes = {
                        # R    G    B
        'red'   : bytes([255,   0,   0]),
        'green' : bytes([0  , 255,   0]),
        'blue'  : bytes([0  ,   0, 255]),
        'aqua'  : bytes([0  , 200,  50]),
        'orange': bytes([255,  50,   0]),
        'white' : bytes([255, 255, 255]),
    }

    # Change the values here if not using an ALT
    def __init__(self):
        vid = int.from_bytes(b'\x04\xD8', 'big')
        pid = int.from_bytes(b'\xEE\xD3', 'big')
        usage_page = int.from_bytes(b'\xFF\x31', 'big')
        usage_id = int.from_bytes(b'\x62', 'big')

        devices = hid.enumerate()
        for device in devices:
            if device['vendor_id'] == vid and device['product_id'] == pid and device['usage_page'] == usage_page and device['usage'] == usage_id:
                self.device = hid.Device(path=device['path'])
                break
        if self.device is None:
            print("[!!] Keyboard not found, quitting.")
            exit(1)

    def close(self):
        self.device.close()

    def send(self, data):
        self.device.write(pad_message(data))

    def get_state(self):
        self.send(tobyte(3))
        state = self.device.read(1) # 1=all, 2=key, 3=under, 4=none
        return state

    def set_state(self, state = b'\x01'):
        data = tobytes([1, state])
        self.send(data)

    def next_animation(self):
        data = tobytes([1, 5])
        self.send(data)

    # Color is a 3-byte array
    def send_notification(self, mode, color, duration = 1):
        if mode not in ['full', 'bottom', 'under']: 
            print("[?] Invalid notification mode, valid options are full, bottom and under.\n[*] Defaulting to full...")
            mode = 'full'
        previous_state = self.get_state()
        if mode == 'bottom':
            data = tobytes([2, 1, color])
        elif mode == 'full':
            data = tobytes([2, 2, color])
        elif mode == 'under':
            data = tobytes([2, 3, color])
        self.send(data)
        sleep(duration)
        self.set_state(previous_state)
        # !!! caller should close the connection

    def send_notification_rgb(self, mode, r, g, b, duration = 1):
        try:
            self.send_notification(mode, tobytes([r, g, b]), duration)
        except ValueError:
            print("[!] RGB values must be 0-255.\n[*] Defaulting to white.")
            self.send_notification(mode, tobytes([255, 255, 255]), duration)

    def send_notification_color(self, mode, name, duration = 1):
        if name not in self.name2bytes:
            print("[?] Unrecognized name. Valid options are:")
            for color in self.name2bytes.keys(): print(f"[-] {color}")
            print("[*] Defaulting to white...")
            name = 'white'
        color = self.name2bytes.get(name)
        self.send_notification(mode, color, duration)

    def set_color(self, color):
        data = tobytes([2, 2, color])
        self.send(data)

    def set_color_rgb(self, r, g, b):
        try:
            self.set_color(tobytes([r, g, b]))
        except ValueError:
            print("[!] RGB values must be 0-255.\n[*] Defaulting to white.")
            self.set_color(tobytes([255, 255, 255]))

    def set_color_name(self, name):
        if name not in self.name2bytes:
            print("[?] Unrecognized name. Valid options are:")
            for color in self.name2bytes.keys(): print(f"[-] {color}")
            print("[*] Defaulting to white...")
            name = 'white'
        color = self.name2bytes.get(name)
        self.set_color(color)