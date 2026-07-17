import time
import cv2
import os
import json
import numpy as np
import threading
import unittest.mock

from pymycobot.mycobot import MyCobot

mycobot_port = os.getenv("MYCOBOT_PORT", "/dev/ttyUSB0")
mycobot_baud = int(os.getenv("MYCOBOT_BAUD", "1000000"))

# --- Robot Arm ---
try:
    mc = MyCobot(mycobot_port, mycobot_baud)
except Exception as e:
    print(f"\n⚠️ <SYSTEM>: Could not connect to MyCobot on {mycobot_port}. Error: {e}")
    mc = unittest.mock.MagicMock()
    mc.get_coords.return_value = [0, 0, 200, -175, 0, -45]
    mc.get_angles.return_value = [0, 0, 0, 0, 0, -45]
    print("\n⚠️ [MOCK MODE] Physical robotic arm not found. Running in simulation mode.")

with open("config.json", "r") as config_file:
    config_data = json.load(config_file)

# --- State Tracking ---
is_holding_object = False
current_held_object = None
known_objects = {}  # Format: {"red block": [150.0, -50.0]}

# --- Gripper ---
def open_gripper():
    global is_holding_object
    mc.set_gripper_value(100, 50)
    is_holding_object = False
    time.sleep(1)

def close_gripper():
    global is_holding_object
    mc.set_gripper_value(0, 50)
    is_holding_object = True
    time.sleep(1)

def BotInit(mc):
    mc.set_fresh_mode(0)
    mc.send_angles([0, 0, 0, 0, 0, -45], 40)
    time.sleep(3)
    mc.send_angles([17.75, -0.79, 0.35, -75, 1.14, -28.12], 40)
    time.sleep(3)

# --- Camera ---
class CameraManager:
    def __init__(self):
        self.cap = None
        self.frame = None
        self.lock = threading.Lock()
        self.running = False

    def start(self):
        # Use V4L2 explicitly to bypass GStreamer and prevent stack smashing on Jetson
        self.cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
        if not self.cap.isOpened():
            self.cap = cv2.VideoCapture(0)
        
        if self.cap.isOpened():
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            # Minimal buffer to prevent memory buildup
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            self.running = True
            threading.Thread(target=self._update, daemon=True).start()

    def _update(self):
        while self.running and self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret and frame is not None and frame.size > 0:
                with self.lock:
                    self.frame = frame.copy()
            time.sleep(0.05)  # ~20fps is enough

    def get_frame(self):
        with self.lock:
            if self.frame is not None:
                return self.frame.copy()
        return None

    def stop(self):
        self.running = False
        if self.cap:
            self.cap.release()
        self.cap = None

cam_manager = CameraManager()
cam_manager.start()

def GetImage():
    frame = cam_manager.get_frame()
    if frame is not None:
        cv2.imwrite("captured_image.jpg", frame)
        print("Image saved as captured_image.jpg")
    else:
        print("Failed to capture image from CameraManager")
