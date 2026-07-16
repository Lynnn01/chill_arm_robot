import time
import cv2
import os
import json
import numpy as np
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

mc = MyCobot('/dev/ttyUSB0', 1000000)

with open("config.json", "r") as config_file:
    config_data = json.load(config_file)

# Open gripper
def open_gripper():
    mc.set_gripper_value(100, 50)
    time.sleep(1)

# Close gripper
def close_gripper():
    mc.set_gripper_value(0, 50)
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

def GetImage():
    capture = cv2.VideoCapture(0, cv2.CAP_V4L2)

    capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)  # Set image width
    capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)  # Set image height
    #capture.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter.fourcc('M', 'J', 'P', 'G'))
    index=1

    if not capture.isOpened():
        print("Cannot open camera")
    else:
        ret, frame = capture.read()
        if ret:
            # Save image
            filename = "captured_image.jpg"
            cv2.imwrite(filename, frame)
            print(f"Image saved as {filename}")
        else:
            print("Failed to capture image")

    # Release camera
    capture.release()
    cv2.destroyAllWindows()
