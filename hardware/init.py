import time
import cv2
import os
import json
import numpy as np
import threading
from pymycobot.mycobot import MyCobot
from pymycobot.genre import Angle
from pymycobot.genre import Coord

from pymycobot import PI_PORT, PI_BAUD

try:
    import RPi.GPIO as GPIO
except Exception as exc:
    GPIO = None
    GPIO_IMPORT_ERROR = exc
else:
    GPIO_IMPORT_ERROR = None
#GPIO.setmode(GPIO.BCM)
    # Pins 20/21 control solenoid valve and air release valve respectively
#GPIO.setup(20, GPIO.OUT)
#GPIO.setup(21, GPIO.OUT)

class MockMyCobot:
    def __init__(self):
        print("\n⚠️ [MOCK MODE] Physical robotic arm not found. Running in simulation mode.")
        self.coords = [0, 0, 200, -175, 0, -45]
        self.angles = [0, 0, 0, 0, 0, -45]
    def send_coords(self, coords, speed, mode=0):
        self.coords = coords
        print(f"🤖 [MOCK] -> Moving to coords: {coords} (speed {speed})")
    def send_angles(self, angles, speed):
        self.angles = angles
        print(f"🤖 [MOCK] -> Moving to angles: {angles} (speed {speed})")
    def get_coords(self):
        return self.coords
    def get_angles(self):
        return self.angles
    def set_gripper_value(self, value, speed):
        print(f"🤖 [MOCK] -> Setting gripper value: {value} (speed {speed})")
    def set_fresh_mode(self, mode):
        print(f"🤖 [MOCK] -> Set fresh mode: {mode}")

mycobot_port = os.getenv("MYCOBOT_PORT", "/dev/ttyUSB0")
mycobot_baud = int(os.getenv("MYCOBOT_BAUD", "1000000"))

try:
    mc = MyCobot(mycobot_port, mycobot_baud)
except Exception as e:
    print(f"\n⚠️ <SYSTEM>: Could not connect to MyCobot on {mycobot_port}. Error: {e}")
    mc = MockMyCobot()

with open("config.json", "r") as config_file:
    config_data = json.load(config_file)

# Gripper state tracking
is_holding_object = False

# Open gripper
def open_gripper():
    global is_holding_object
    mc.set_gripper_value(100, 50)
    is_holding_object = False
    time.sleep(1)

# Close gripper
def close_gripper():
    global is_holding_object
    mc.set_gripper_value(0, 50)
    is_holding_object = True
    time.sleep(1)


def pump_on():
    if GPIO is None:
        raise RuntimeError(f"GPIO is unavailable: {GPIO_IMPORT_ERROR}")
    # Open solenoid valve
    GPIO.output(20, 0)


# Stop suction pump
def pump_off():
    if GPIO is None:
        raise RuntimeError(f"GPIO is unavailable: {GPIO_IMPORT_ERROR}")
    # Close solenoid valve
    GPIO.output(20, 1)
    time.sleep(0.05)
    # Open air release valve
    GPIO.output(21, 0)
    time.sleep(1)
    GPIO.output(21, 1)
    time.sleep(0.05)

def BotInit(mc):
    mc.set_fresh_mode(0)

    mc.send_angles([0, 0, 0, 0, 0, -45], 40)
    time.sleep(3)

    mc.send_angles([17.75, -0.79, 0.35, -75, 1.14, -28.12], 40)
    time.sleep(3)

class CameraManager:
    def __init__(self):
        self.cap = None
        self.frame = None
        self.lock = threading.Lock()
        self.running = False

    def start(self):
        # On Windows, try cv2.CAP_DSHOW, on Linux CAP_V4L2. Try default first.
        self.cap = cv2.VideoCapture(0) 
        if not self.cap.isOpened():
            self.cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
        
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.running = True
        threading.Thread(target=self._update, daemon=True).start()

    def _update(self):
        while self.running and self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                with self.lock:
                    self.frame = frame.copy()
            time.sleep(0.03)

    def get_frame(self):
        with self.lock:
            if self.frame is not None:
                return self.frame.copy()
        return None

    def stop(self):
        self.running = False
        if self.cap:
            self.cap.release()

cam_manager = CameraManager()
cam_manager.start()

def GetImage():
    frame = cam_manager.get_frame()
    if frame is not None:
        filename = "captured_image.jpg"
        cv2.imwrite(filename, frame)
        print(f"Image saved as {filename}")
    else:
        print("Failed to capture image from CameraManager")
