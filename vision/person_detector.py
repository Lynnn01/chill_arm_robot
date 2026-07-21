import os
import time
import threading
from hardware import init
from hardware.init import cam_manager
import armconfig

_models = {}
_current_mode = "ARM Mode"
_is_active = False
_thread = None
_target_angles = armconfig.POSE_HOME.copy()
_last_send_time = 0

def get_model(mode_name):
    if mode_name == "Person Detect":
        filename = "person.pt"
    elif mode_name == "Face Detect":
        filename = "face.pt"
    else:
        return None
        
    if mode_name not in _models:
        try:
            from ultralytics import YOLO
            model_path = os.path.join(init.PROJECT_ROOT, "vision", "models", filename)
            if os.path.exists(model_path):
                print(f"🤖 <SYSTEM>: Loading {filename} model...")
                _models[mode_name] = YOLO(model_path)
            else:
                print(f"⚠️ <SYSTEM>: ไม่พบโมเดล YOLO ที่ {model_path}")
                return None
        except ImportError:
            print("⚠️ <SYSTEM>: ไม่พบไลบรารี ultralytics (pip install ultralytics)")
            return None
    return _models.get(mode_name)

def _detection_loop():
    """Background thread that runs inference on camera frames."""
    global _is_active, _current_mode
    while _is_active:
        if not _is_active or _current_mode == "ARM Mode":
            break
            
        model = get_model(_current_mode)
        if not model:
            time.sleep(2)
            continue
            
        frame = cam_manager.frame
        if frame is not None and frame.size > 0:
            # Create a copy so we don't modify the raw feed while inference is running
            img = frame.copy()
            # Run inference (suppress verbose output to avoid spam)
            results = model(img, verbose=False)
            
            # Draw bounding boxes
            annotated_frame = results[0].plot()
            
            # --- FACE/PERSON TRACKING LOGIC ---
            if _current_mode in ["Face Detect", "Person Detect"] and len(results) > 0:
                boxes = results[0].boxes
                if len(boxes) > 0:
                    largest_box = None
                    max_area = 0
                    for box in boxes:
                        x1, y1, x2, y2 = box.xyxy[0].tolist()
                        area = (x2 - x1) * (y2 - y1)
                        if area > max_area:
                            max_area = area
                            largest_box = (x1, y1, x2, y2)
                    
                    if largest_box:
                        x1, y1, x2, y2 = largest_box
                        cx = (x1 + x2) / 2.0
                        cy = (y1 + y2) / 2.0
                        
                        img_h, img_w = img.shape[:2]
                        center_x = img_w / 2.0
                        center_y = img_h / 2.0
                        
                        pan_error = center_x - cx
                        tilt_error = center_y - cy
                        
                        # Deadzone of 20 pixels to prevent jitter
                        if abs(pan_error) > armconfig.TRACKING_DEADZONE_PX or abs(tilt_error) > armconfig.TRACKING_DEADZONE_PX:
                            global _target_angles, _last_send_time
                            Kp = armconfig.TRACKING_KP # Slightly faster response
                            
                            # Increase J1 turns left. If person is on left (cx < center_x), pan_error > 0.
                            new_j1 = _target_angles[0] + (pan_error * Kp)
                            # Increase J4 tilts up/down. We will guess positive tilts up.
                            new_j4 = _target_angles[3] + (tilt_error * Kp)
                            
                            # Clamp safety limits
                            new_j1 = max(armconfig.TRACKING_J1_MIN, min(armconfig.TRACKING_J1_MAX, new_j1))
                            new_j4 = max(armconfig.TRACKING_J4_MIN, min(armconfig.TRACKING_J4_MAX, new_j4))
                            
                            if abs(new_j1 - _target_angles[0]) > 0.5 or abs(new_j4 - _target_angles[3]) > 0.5:
                                _target_angles[0] = new_j1
                                _target_angles[3] = new_j4
                                
                                # Rate limit sending commands to max 10 times a second to prevent serial choke
                                if time.time() - _last_send_time > armconfig.TRACKING_SEND_INTERVAL:
                                    init.mc.send_angles(_target_angles, armconfig.SPEED_TRACKING) # Speed 60 for smoother/faster tracking
                                    _last_send_time = time.time()
            # ---------------------------
            
            # Set it back to the cam_manager overlay so it displays on the GUI
            cam_manager.set_overlay(annotated_frame, duration=1.0)
            
        # Give some breathing room for CPU/UI
        time.sleep(0.05)
        
    print("🤖 <SYSTEM>: Background Detection stopped.")

def set_detect_mode(new_mode: str):
    """Change the background detection mode."""
    global _is_active, _thread, _current_mode, _target_angles
    
    _current_mode = new_mode
    
    if new_mode in ["Face Detect", "Person Detect"]:
        print(f"🤖 <SYSTEM>: Resetting posture for {new_mode} Tracking...")
        _target_angles = armconfig.POSE_HOME.copy()
        init.mc.send_angles(_target_angles, armconfig.SPEED_RESET)
    
    if new_mode in ["Person Detect", "Face Detect"] and not _is_active:
        print(f"🤖 <SYSTEM>: {new_mode} started.")
        _is_active = True
        _thread = threading.Thread(target=_detection_loop, daemon=True)
        _thread.start()
        
    elif new_mode == "ARM Mode" and _is_active:
        _is_active = False
        # The thread will naturally exit on the next loop iteration
