import os
import time
import threading
from hardware import init
from hardware.init import cam_manager

_model = None
_is_active = False
_thread = None

def get_person_model():
    global _model
    if _model is None:
        try:
            from ultralytics import YOLO
            model_path = os.path.join(init.PROJECT_ROOT, "vision", "models", "person.pt")
            if os.path.exists(model_path):
                print("🤖 <SYSTEM>: Loading person.pt model...")
                _model = YOLO(model_path)
            else:
                print(f"⚠️ <SYSTEM>: ไม่พบโมเดล YOLO ที่ {model_path}")
        except ImportError:
            print("⚠️ <SYSTEM>: ไม่พบไลบรารี ultralytics (pip install ultralytics)")
    return _model

def _detection_loop():
    """Background thread that runs inference on camera frames."""
    global _is_active
    while _is_active:
        if not _is_active:
            break
            
        model = get_person_model()
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
        
    print("🤖 <SYSTEM>: Person Detection stopped.")

def set_person_detect_mode(active: bool):
    """Enable or disable the background person detection loop."""
    global _is_active, _thread
    
    if active and not _is_active:
        print("🤖 <SYSTEM>: Person Detection started.")
        _is_active = True
        _thread = threading.Thread(target=_detection_loop, daemon=True)
        _thread.start()
        
    elif not active and _is_active:
        _is_active = False
        # The thread will naturally exit on the next loop iteration
