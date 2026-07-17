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

import unittest.mock

mycobot_port = os.getenv("MYCOBOT_PORT", "/dev/ttyUSB0")
mycobot_baud = int(os.getenv("MYCOBOT_BAUD", "1000000"))

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

# Gripper state tracking
is_holding_object = False
current_held_object = None

# Object memory tracking
# Format: {"red block": [150.0, -50.0], "blue block": "in gripper"}
known_objects = {}

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

# (Deleted legacy pump functions)

def BotInit(mc):
    mc.set_fresh_mode(0)

    mc.send_angles([0, 0, 0, 0, 0, -45], 40)
    time.sleep(3)

    mc.send_angles([17.75, -0.79, 0.35, -75, 1.14, -28.12], 40)
    time.sleep(3)

def GetImage():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
    
    if cap.isOpened():
        # Read a few frames to allow camera to adjust white balance/exposure
        for _ in range(3):
            ret, frame = cap.read()
            time.sleep(0.1)
            
        ret, frame = cap.read()
        if ret:
            cv2.imwrite("captured_image.jpg", frame)
            print("Image saved as captured_image.jpg")
        else:
            print("Failed to read frame from Camera")
        cap.release()
    else:
        print("Failed to open Camera")
