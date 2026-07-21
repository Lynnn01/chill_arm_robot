from vision import yolo_detector

def scan_with_yolo(object_name: str) -> list | None:
    """Fast scan using YOLO directly"""
    return yolo_detector.scan_with_yolo(object_name)
