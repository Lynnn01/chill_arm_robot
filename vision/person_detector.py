import os
import time
import threading
from hardware import init
from hardware.init import cam_manager

_models = {}
_current_mode = "ARM Mode"
_is_active = False
_thread = None

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
            
            # Set it back to the cam_manager overlay so it displays on the GUI
            cam_manager.set_overlay(annotated_frame, duration=1.0)
            
        # Give some breathing room for CPU/UI
        time.sleep(0.05)
        
    print("🤖 <SYSTEM>: Background Detection stopped.")

def set_detect_mode(new_mode: str):
    """Change the background detection mode."""
    global _is_active, _thread, _current_mode
    
    _current_mode = new_mode
    
    if new_mode in ["Person Detect", "Face Detect"] and not _is_active:
        print(f"🤖 <SYSTEM>: {new_mode} started.")
        _is_active = True
        _thread = threading.Thread(target=_detection_loop, daemon=True)
        _thread.start()
        
    elif new_mode == "ARM Mode" and _is_active:
        _is_active = False
        # The thread will naturally exit on the next loop iteration
