import os
from PIL import Image
from hardware import init
from vision import api, eyeonhand, yolo_detector
from .config_loader import load_offsets
from .coord_transform import apply_rotation, clamp_xy

def find_object_coord(object_name: str, j1_deg: float = 0) -> list | None:
    """
    ค้นหาพิกัดวัตถุจากภาพปัจจุบัน
    1. ลอง YOLO ก่อน (เร็ว)
    2. Fallback ไป Qwen Vision AI (ช้า แต่แม่น)
    Returns: [x, y] หรือ None
    """
    offsets = load_offsets()

    # Fast path: YOLO
    yolo_coord = yolo_detector.scan_with_yolo(object_name)
    if yolo_coord:
        return yolo_coord

    # Slow path: Qwen
    init.GetImage()
    img_path = os.path.join(init.PROJECT_ROOT, "captured_image.jpg")
    width, height = Image.open(img_path).size
    positions = api.QwenVLRequest("a " + object_name, img_path).get("coordinates", [])

    if not positions:
        return None

    pos = positions[0]
    cx = (pos["x1"] + pos["x2"]) / 2 / 1000 * width
    cy = (pos["y1"] + pos["y2"]) / 2 / 1000 * height
    
    import armconfig
    if getattr(armconfig, 'CAMERA_FLIP_HORIZONTAL', False):
        cx = width - cx
        
    coord_np = eyeonhand.pixel_to_arm((cx, cy))
    coord = [float(coord_np[0]) + offsets["x"], float(coord_np[1]) + offsets["y"]]

    if j1_deg != 0:
        coord = apply_rotation(coord, j1_deg)

    return clamp_xy(coord)
