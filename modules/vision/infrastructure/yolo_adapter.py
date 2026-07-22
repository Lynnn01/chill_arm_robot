"""
modules/vision/infrastructure/yolo_adapter.py
Infrastructure Layer: Adapter implementing VisionDetectorPort via vision.yolo_detector
"""

from typing import Optional, List
from vision.yolo_detector import scan_with_yolo
from modules.vision.domain.calibration import BoundingBox
from modules.vision.application.ports import VisionDetectorPort

class YoloVisionAdapter(VisionDetectorPort):
    """Adapter wrapping YOLO object detection."""

    def scan_with_yolo(self, target_name: str) -> Optional[List[float]]:
        return scan_with_yolo(target_name)

    def detect_objects(self, img) -> List[BoundingBox]:
        return []
