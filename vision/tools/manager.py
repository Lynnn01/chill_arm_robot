import time
import threading
from hardware import init
from hardware.init import cam_manager
import armconfig

# Import individual detectors
from vision.tools.face_detector.index import process_frame as face_process
from vision.tools.person_detector.index import process_frame as person_process
from vision.tools.cube_detector.index import process_frame as cube_process

_current_mode = "ARM Mode"
_is_active = False
_thread = None
_target_angles = armconfig.POSE_HOME.copy()
_last_send_time = 0

def _detection_loop():
    """Background thread that runs inference on camera frames."""
    global _is_active, _current_mode, _target_angles, _last_send_time
    
    while _is_active:
        if not _is_active or _current_mode == "ARM Mode":
            break
            
        frame = cam_manager.frame
        if frame is not None and frame.size > 0:
            # Create a copy so we don't modify the raw feed while inference is running
            img = frame.copy()
            
            # Delegate to specific tools based on mode
            if _current_mode == "Face Detect":
                annotated_frame, _target_angles, _last_send_time = face_process(img, _target_angles, _last_send_time)
            elif _current_mode == "Person Detect":
                annotated_frame, _target_angles, _last_send_time = person_process(img, _target_angles, _last_send_time)
            elif _current_mode == "Cube Detect":
                annotated_frame, _target_angles, _last_send_time = cube_process(img, _target_angles, _last_send_time)
            else:
                annotated_frame = img
            
            # Set it back to the cam_manager overlay so it displays on the GUI
            cam_manager.set_overlay(annotated_frame, duration=1.0)
            
        # Give some breathing room for CPU/UI
        time.sleep(0.05)
        
    print("🤖 <SYSTEM>: Background Detection stopped.")

def set_detect_mode(new_mode: str):
    """Change the background detection mode."""
    global _is_active, _thread, _current_mode, _target_angles
    
    _current_mode = new_mode
    
    if new_mode in ["Face Detect", "Person Detect", "Cube Detect"]:
        print(f"🤖 <SYSTEM>: Resetting posture for {new_mode} Tracking...")
        _target_angles = armconfig.POSE_HOME.copy()
        init.mc.send_angles(_target_angles, armconfig.SPEED_RESET)
    
    if new_mode in ["Person Detect", "Face Detect", "Cube Detect"] and not _is_active:
        print(f"🤖 <SYSTEM>: {new_mode} started.")
        _is_active = True
        _thread = threading.Thread(target=_detection_loop, daemon=True)
        _thread.start()
        
    elif new_mode == "ARM Mode" and _is_active:
        _is_active = False
        # The thread will naturally exit on the next loop iteration
