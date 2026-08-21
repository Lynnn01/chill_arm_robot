import time
import cv2
import os
import sys
import json
import threading
import armconfig
import unittest.mock

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# ---------------------------------------------------------------------------
# Platform-aware robot arm import
# ---------------------------------------------------------------------------
# ลำดับการตัดสินใจเลือก platform:
#   1. MYCOBOT_PLATFORM=windows  → ใช้ MyCobot280 (COM port)
#   2. MYCOBOT_PLATFORM=linux    → ใช้ MyCobot (ttyUSB0)
#   3. ไม่กำหนด                 → auto-detect จาก sys.platform
# ---------------------------------------------------------------------------
import contextlib

_platform_override = os.getenv("MYCOBOT_PLATFORM", "").lower()
_is_windows = _platform_override == "windows" or (
    _platform_override == "" and sys.platform == "win32"
)

if _is_windows:
    with contextlib.redirect_stdout(open(os.devnull, 'w')):
        from pymycobot.mycobot280 import MyCobot280 as _MyCobotClass

    _default_port = os.getenv("MYCOBOT_PORT", "COM9")
    print("[init] Platform: Windows -> using MyCobot280")
else:
    with contextlib.redirect_stdout(open(os.devnull, 'w')):
        from pymycobot.mycobot import MyCobot as _MyCobotClass

    _default_port = "/dev/ttyUSB0"
    print("[init] Platform: Linux/Jetson -> using MyCobot")

mycobot_port = os.getenv("MYCOBOT_PORT", _default_port)
mycobot_baud = int(os.getenv("MYCOBOT_BAUD", "1000000"))

# --- Robot Arm ---
# Single global lock for all serial communication to prevent race conditions
_mc_lock = threading.Lock()


class LockedMyCobot:
    """Wraps MyCobot/MyCobot280 with a global lock to prevent concurrent Serial access."""

    def __init__(self, port, baud):
        with contextlib.redirect_stdout(open(os.devnull, 'w')):
            self._mc = _MyCobotClass(port, baud)

    def _call(self, method, *args, **kwargs):
        with _mc_lock:
            return getattr(self._mc, method)(*args, **kwargs)

    def send_angles(self, angles, speed):
        return self._call("send_angles", angles, speed)

    def send_angle(self, id, degree, speed):
        return self._call("send_angle", id, degree, speed)

    def send_coords(self, coords, speed, mode=0):
        self._last_coords = (coords, speed, mode)
        return self._call("send_coords", coords, speed, mode)

    def get_coords(self):
        return self._call("get_coords")

    def get_angles(self):
        return self._call("get_angles")

    def safe_get_coords(self, retries=3):
        """Robust wrapper for get_coords that handles None or empty returns."""
        for _ in range(retries):
            coords = self.get_coords()
            if coords and len(coords) >= 6 and any(c != 0 for c in coords):
                return coords
            time.sleep(0.1)
        return None

    def safe_get_angles(self, retries=3):
        """Robust wrapper for get_angles."""
        for _ in range(retries):
            res = self.get_angles()
            if res and isinstance(res, list) and len(res) >= 6:
                return res
            time.sleep(0.1)
        return None

    def wait_for_arrival(self, target, timeout=3.5, threshold=25.0, mode="coords"):
        """
        บล็อกรอจนกว่าปลายแขนกลจะเคลื่อนที่ถึงพิกัดเป้าหมาย
        mode="coords" หรือ "angles"
        """
        start_time = time.time()
        time.sleep(0.4)

        # สำหรับ coords ให้เทียบเฉพาะตำแหน่ง X,Y,Z 3 ค่าแรก (ไม่นำมุมหมุน Rx,Ry,Rz มาบวกกัน)
        target_check = target[:3] if mode == "coords" else target

        while time.time() - start_time < timeout:
            current = self.safe_get_coords() if mode == "coords" else self.safe_get_angles()
            if current is None:
                time.sleep(0.15)
                continue
            
            try:
                check_curr = current[:len(target_check)]
                diff = sum(abs(c - t) for c, t in zip(check_curr, target_check))
                if diff <= threshold:
                    return True
            except Exception:
                pass
            
            time.sleep(0.15)
        
        return True

    def wait_for_z(self, target_z, timeout=10.0, threshold=8.0):
        """
        รอแกน Z ดำดิ่งถึงระดับเป้าหมาย — หากหัวยังค้างกลางอากาศจะส่งคำสั่งย้ำให้อัตโนมัติ
        """
        start_time = time.time()
        time.sleep(0.4)
        last_resend = 0.0

        while time.time() - start_time < timeout:
            current = self.safe_get_coords()
            if current and len(current) >= 3:
                z_now = current[2]
                # ตรวจจับว่าลงถึงระดับความสูงเป้าหมายจริง (คลาดเคลื่อนไม่เกิน 8mm หรือแตะระดับเป้า)
                if abs(z_now - target_z) <= threshold or (z_now <= target_z + 3.0 and z_now >= target_z - 15.0):
                    print(f"✅ <SYSTEM>: หัวลงถึงระดับเป้าหมาย Z={z_now:.1f} (เป้า {target_z})")
                    return True

                # ส่งคำสั่งซ้ำทุก 1.5 วิ ถ้า Z ยังค้างอยู่สูงกว่าเป้าเกิน 15mm
                elapsed = time.time() - start_time
                if z_now > target_z + 15.0 and elapsed - last_resend > 1.5:
                    print(f"🔄 <SYSTEM>: Z={z_now:.1f} ยังค้างสูงกว่าเป้า {target_z} — ส่งคำสั่งดิ่งลงซ้ำ!")
                    last_resend = elapsed
                    if hasattr(self, "_last_coords") and self._last_coords:
                        coords, speed, mode = self._last_coords
                        self._call("send_coords", coords, speed, mode)

            time.sleep(0.2)

        # Timeout — ตรวจสอบครั้งสุดท้ายว่าถึงหรือไม่ก่อน return
        current = self.safe_get_coords()
        if current and len(current) >= 3:
            z_now = current[2]
            if abs(z_now - target_z) <= threshold + 5.0:
                print(f"✅ <SYSTEM>: Timeout แต่ Z={z_now:.1f} ใกล้เป้า {target_z} พอ — ถือว่าถึง")
                return True
            print(f"⚠️ <SYSTEM>: Timeout! Z={z_now:.1f} ยังไม่ถึงเป้า {target_z} (threshold={threshold})")
            return False

        # ถ้าอ่านค่า Z ไม่ได้เลย ให้ถือว่าถึง (MOCK / Hardware ตอบสนองช้า)
        print(f"⚠️ <SYSTEM>: ไม่สามารถอ่าน Z ได้ — ถือว่าถึงระดับเป้า (Z_target={target_z})")
        return True


    def set_gripper_value(self, value, speed):
        return self._call("set_gripper_value", value, speed)

    def get_gripper_value(self):
        if hasattr(self._mc, "get_gripper_value"):
            try:
                return self._call("get_gripper_value")
            except Exception:
                return None
        return None

    def set_gripper_state(self, state, speed):
        if hasattr(self._mc, "set_gripper_state"):
            try:
                return self._call("set_gripper_state", state, speed)
            except Exception:
                pass
        return None

    def set_fresh_mode(self, mode):
        if hasattr(self._mc, "set_fresh_mode"):
            return self._call("set_fresh_mode", mode)
        return None

    def power_on(self):
        return self._call("power_on")

    def set_color(self, r, g, b):
        return self._call("set_color", r, g, b)

    def release_all_servos(self):
        return self._call("release_all_servos")


try:
    mc = LockedMyCobot(mycobot_port, mycobot_baud)
    print(
        f"✅ Connected to {'MyCobot280' if _is_windows else 'MyCobot'} on {mycobot_port}"
    )
except Exception as e:
    print(f"\n[WARNING] <SYSTEM>: Could not connect on {mycobot_port}. Error: {e}")
    mc = unittest.mock.MagicMock()
    mc.get_coords.return_value = [0, 0, 200, -175, 0, -45]
    mc.get_angles.return_value = [0, 0, 0, 0, 0, -45]
    print(
        "\n[WARNING] [MOCK MODE] Physical robotic arm not found. Running in simulation mode."
    )

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
    print("🤖 <SYSTEM>: กำลังเปิดกริปเปอร์เพื่อปล่อยวัตถุ...")
    for attempt in range(3):
        try:
            mc.set_gripper_value(100, 60)
            if hasattr(mc, "set_gripper_state"):
                mc.set_gripper_state(0, 60)
        except Exception as e:
            print(f"⚠️ <SYSTEM>: ส่งคำสั่งเปิดกริปเปอร์ผิดพลาด: {e}")
        time.sleep(0.6)

        val = None
        try:
            if hasattr(mc, "get_gripper_value"):
                val = mc.get_gripper_value()
        except Exception:
            val = None

        if val is not None and isinstance(val, (int, float)) and val >= 70:
            print(f"✅ <SYSTEM>: กริปเปอร์เปิดสุดแล้ว (val={val})")
            break
        elif val is not None and isinstance(val, (int, float)):
            if attempt < 2:
                print(f"⚠️ <SYSTEM>: กริปเปอร์ยังไม่เปิดสุด (val={val}) — ส่งคำสั่งเปิดซ้ำครั้งที่ {attempt+2}...")
        time.sleep(0.2)

    is_holding_object = False
    time.sleep(0.4)


def close_gripper():
    global is_holding_object
    print("🤖 <SYSTEM>: กำลังปิดกริปเปอร์เพื่อจับวัตถุ...")
    for attempt in range(2):
        try:
            mc.set_gripper_value(0, 60)
            if hasattr(mc, "set_gripper_state"):
                mc.set_gripper_state(1, 60)
        except Exception as e:
            print(f"⚠️ <SYSTEM>: ส่งคำสั่งปิดกริปเปอร์ผิดพลาด: {e}")
        time.sleep(0.5)

    is_holding_object = True
    time.sleep(0.5)


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
        mc.send_angles(armconfig.POSE_HOME, armconfig.SPEED_GRAB)
        time.sleep(3)
        print("Moving to Ready position...")
        mc.send_angles(armconfig.POSE_READY, armconfig.SPEED_GRAB)
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
        self.ai_results = None
        self.ai_expiry = 0

    def set_ai_results(self, results, duration=0.5):
        with self.lock:
            self.ai_results = results
            self.ai_expiry = time.time() + duration

    def set_overlay(self, frame, duration=1.0):
        # Kept for backward compatibility without freezing live feed
        pass

    def start(self):
        if self._started:
            return
        self._started = True

        # Initialize VideoCapture in the MAIN thread to avoid OpenCV Qt plugin crashes on Jetson
        try:
            cam_idx_env = os.getenv("CAMERA_INDEX")
            preferred_idx = int(cam_idx_env) if cam_idx_env is not None and cam_idx_env.isdigit() else 0
            
            if _is_windows:
                cap = cv2.VideoCapture(preferred_idx, cv2.CAP_DSHOW)
                if not cap.isOpened() and preferred_idx == 0:
                    cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)
                if not cap.isOpened():
                    cap = cv2.VideoCapture(preferred_idx)
            else:
                # Try V4L2 first (bypasses GStreamer), prefer index 0 on Jetson
                os.environ["OPENCV_LOG_LEVEL"] = "FATAL" # Suppress OpenCV warnings temporarily
                cap = cv2.VideoCapture(preferred_idx, cv2.CAP_V4L2)
                if not cap.isOpened() and preferred_idx == 0:
                    cap = cv2.VideoCapture(1, cv2.CAP_V4L2)
                if not cap.isOpened():
                    cap = cv2.VideoCapture(preferred_idx)
                os.environ["OPENCV_LOG_LEVEL"] = "WARNING" # Restore

            if not cap.isOpened():
                print("⚠️ Camera not available. Running without camera feed.")
                return

            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

            self.cap = cap
            self.running = True
            print("✅ Camera started (Zero-Lag Buffer Mode).")

            # Start high-speed reading loop in a background thread
            threading.Thread(target=self._update, daemon=True).start()
        except Exception as e:
            print(f"⚠️ Camera init failed: {e}")

    def _update(self):
        """Dedicated high-speed thread to constantly drain hardware buffer and keep the latest frame."""
        while self.running and self.cap and self.cap.isOpened():
            try:
                grabbed = self.cap.grab()
                if grabbed:
                    ret, frame = self.cap.retrieve()
                    if ret and frame is not None and frame.size > 0:
                        # พลิกภาพซ้ายขวาถ้าตั้งค่าไว้ใน armconfig
                        if getattr(armconfig, 'CAMERA_FLIP_HORIZONTAL', False):
                            frame = cv2.flip(frame, 1)
                        with self.lock:
                            self.frame = frame
                else:
                    time.sleep(0.005)
            except Exception as e:
                print(f"⚠️ Camera read error: {e}")
                time.sleep(0.01)

    def get_frame(self):
        """Returns the latest live video frame with real-time AI overlay."""
        with self.lock:
            if self.frame is not None:
                img = self.frame.copy()
                
                # Draw live AI bounding boxes dynamically on the newest frame
                if self.ai_results is not None and time.time() < self.ai_expiry:
                    try:
                        img = self.ai_results.plot(img=img)
                    except Exception:
                        pass
                
                return img
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


def set_gripper_value(value, speed=80):
    return mc.set_gripper_value(value, speed)
