"""
modules/vision/application/ports.py
Application Layer: Ports (Interfaces) for Vision Services
"""

from typing import Protocol, Optional, List
from modules.vision.domain.calibration import PixelCoordinate, BoundingBox

class VisionDetectorPort(Protocol):
    """Hexagonal Port Interface for Computer Vision Object Detection."""

    def scan_with_yolo(self, target_name: str) -> Optional[List[float]]:
        ...

    def detect_objects(self, img) -> List[BoundingBox]:
        ...
