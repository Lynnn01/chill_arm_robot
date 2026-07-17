import time
import cv2
import os
import sys
import json
import threading
import unittest.mock

# ---------------------------------------------------------------------------
# Platform-aware robot arm import
# ---------------------------------------------------------------------------
# ลำดับการตัดสินใจเลือก platform:
#   1. MYCOBOT_PLATFORM=windows  → ใช้ MyCobot280 (COM port)
#   2. MYCOBOT_PLATFORM=linux    → ใช้ MyCobot (ttyUSB0)
#   3. ไม่กำหนด                 → auto-detect จาก sys.platform
# ---------------------------------------------------------------------------
_platform_override = os.getenv("MYCOBOT_PLATFORM", "").lower()
_is_windows = (
    _platform_override == "windows"
    or (_platform_override == "" and sys.platform == "win32")
)

if _is_windows:
    from pymycobot.mycobot280 import MyCobot280 as _MyCobotClass
    _default_port = "COM10"
    print("[init] Platform: Windows → using MyCobot280")
else:
    from pymycobot.mycobot import MyCobot as _MyCobotClass
    _default_port = "/dev/ttyUSB0"
    print("[init] Platform: Linux/Jetson → using MyCobot")

mycobot_port = os.getenv("MYCOBOT_PORT", _default_port)
mycobot_baud = int(os.getenv("MYCOBOT_BAUD", "1000000"))

# --- Robot Arm ---
# Single global lock for all serial communication to prevent race conditions
_mc_lock = threading.Lock()

class LockedMyCobot:
    """Wraps MyCobot/MyCobot280 with a global lock to prevent concurrent Serial access."""
    def __init__(self, port, baud):
        self._mc = _MyCobotClass(port, baud)

    def _call(self, method, *args, **kwargs):
        with _mc_lock:
            return getattr(self._mc, method)(*args, **kwargs)

    def send_angles(self, angles, speed): return self._call("send_angles", angles, speed)
    def send_angle(self, id, degree, speed): return self._call("send_angle", id, degree, speed)
    def send_coords(self, coords, speed, mode=0): return self._call("send_coords", coords, speed, mode)
    def get_coords(self): return self._call("get_coords")
    def get_angles(self): return self._call("get_angles")
    def set_gripper_value(self, value, speed): return self._call("set_gripper_value", value, speed)
    def set_fresh_mode(self, mode): return self._call("set_fresh_mode", mode)
    def power_on(self): return self._call("power_on")
    def set_color(self, r, g, b): return self._call("set_color", r, g, b)
    def release_all_servos(self): return self._call("release_all_servos")

try:
    mc = LockedMyCobot(mycobot_port, mycobot_baud)
    print(f"✅ Connected to {'MyCobot280' if _is_windows else 'MyCobot'} on {mycobot_port}")
except Exception as e:
    print(f"\n⚠️ <SYSTEM>: Could not connect on {mycobot_port}. Error: {e}")
    mc = unittest.mock.MagicMock()
    mc.get_coords.return_value = [0, 0, 200, -175, 0, -45]
    mc.get_angles.return_value = [0, 0, 0, 0, 0, -45]
    print("\n⚠️ [MOCK MODE] Physical robotic arm not found. Running in simulation mode.")

_HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(_HERE, ".."))
CONFIG_PATH = os.path.join(PROJECT_ROOT, "config.json")

try:
    with open(CONFIG_PATH, "r", encoding="utf-8") as config_file:
        config_data = json.load(config_file)
except Exception:
    config_data = {}

# --- State Tracking ---
is_holding_object = False
current_held_object = None
known_objects = {}  # Format: {"red block": [150.0, -50.0]}
last_coords = [0, 0, 200, -175, 0, -45]

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
    try:
        # Windows (MyCobot280) ใช้ fresh_mode(1) + power_on ก่อน
        if _is_windows:
            mc.set_fresh_mode(1)
            time.sleep(0.2)
            mc.power_on()
            time.sleep(0.5)
        else:
            mc.set_fresh_mode(0)

        print("Moving to Home position...")
        mc.send_angles([0, 0, 0, 0, 0, -45], 40)
        time.sleep(3)
        print("Moving to Ready position...")
        mc.send_angles([17.75, -0.79, 0.35, -75, 1.14, -28.12], 40)
        time.sleep(3)
    except Exception as e:
        print(f"⚠️ BotInit error (non-fatal): {e}")

# --- Camera ---
class CameraManager:
    def __init__(self):
        self.cap = None
        self.frame = None
        self.lock = threading.Lock()
        self.running = False
        self._started = False

    def start(self):
        if self._started:
            return
        self._started = True
        
        # Initialize VideoCapture in the MAIN thread to avoid OpenCV Qt plugin crashes on Jetson
        try:
            # Try V4L2 first (bypasses GStreamer)
            cap = cv2.VideoCapture(1, cv2.CAP_V4L2)
            if not cap.isOpened():
                cap = cv2.VideoCapture(1)
            
            if not cap.isOpened():
                print("⚠️ Camera not available. Running without camera feed.")
                return
            
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            
            self.cap = cap
            self.running = True
            print("✅ Camera started.")
            
            # Start only the reading loop in a background thread
            threading.Thread(target=self._update, daemon=True).start()
        except Exception as e:
            print(f"⚠️ Camera init failed: {e}")

    def _update(self):
        while self.running and self.cap and self.cap.isOpened():
            try:
                ret, frame = self.cap.read()
                if ret and frame is not None and frame.size > 0:
                    with self.lock:
                        self.frame = frame
            except Exception as e:
                print(f"⚠️ Camera read error: {e}")
            time.sleep(0.04)  # ~25 fps

    def get_frame(self):
        with self.lock:
            if self.frame is not None:
                return self.frame.copy()
        return None

    def stop(self):
        self.running = False
        time.sleep(0.15)
        if self.cap:
            self.cap.release()
        self.cap = None

cam_manager = CameraManager()
# NOTE: cam_manager.start() is called from start_gui() AFTER tkinter is ready

def GetImage():
    frame = cam_manager.get_frame()
    if frame is not None:
        img_path = os.path.join(PROJECT_ROOT, "captured_image.jpg")
        cv2.imwrite(img_path, frame)
        print(f"Image saved as {img_path}")
    else:
        print("Failed to capture image from CameraManager")
