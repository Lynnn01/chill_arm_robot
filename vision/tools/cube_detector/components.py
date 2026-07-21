import os
from hardware import init
from vision.tools.shares.tracking_logic import calculate_and_move

_model = None

def get_model():
    global _model
    if _model is None:
        try:
            from ultralytics import YOLO
            model_path = os.path.join(init.PROJECT_ROOT, "vision", "models", "cube.pt")
            if os.path.exists(model_path):
                _model = YOLO(model_path)
            else:
                print(f"⚠️ <SYSTEM>: ไม่พบโมเดล YOLO ที่ {model_path}")
        except ImportError:
            pass
    return _model

def detect_and_track(img, target_angles, last_send_time):
    model = get_model()
    if not model:
        return img, target_angles, last_send_time

    results = model(img, verbose=False)
    annotated_frame = results[0].plot() if len(results) > 0 else img
    
    if len(results) > 0:
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
                
                target_angles, last_send_time = calculate_and_move(cx, cy, center_x, center_y, target_angles, last_send_time)
                
    return annotated_frame, target_angles, last_send_time
