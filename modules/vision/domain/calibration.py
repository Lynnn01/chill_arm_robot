"""
modules/vision/domain/calibration.py
Domain Layer: Value Objects & Domain Rules for Vision Calibration & Bounding Boxes
"""

from typing import Tuple

class PixelCoordinate:
    """Value Object representing a 2D Pixel Coordinate (U, V). Immutable."""
    def __init__(self, u: float, v: float):
        self._u = float(u)
        self._v = float(v)

    @property
    def u(self) -> float:
        return self._u

    @property
    def v(self) -> float:
        return self._v

    def to_tuple(self) -> Tuple[float, float]:
        return (self._u, self._v)

    def __repr__(self) -> str:
        return f"PixelCoordinate(u={self._u:.1f}, v={self._v:.1f})"

class BoundingBox:
    """Value Object representing an Object Detection Bounding Box."""
    def __init__(self, x1: float, y1: float, x2: float, y2: float, label: str, confidence: float):
        self._x1 = float(x1)
        self._y1 = float(y1)
        self._x2 = float(x2)
        self._y2 = float(y2)
        self._label = label
        self._confidence = float(confidence)

    @property
    def center(self) -> PixelCoordinate:
        return PixelCoordinate((self._x1 + self._x2) / 2.0, (self._y1 + self._y2) / 2.0)

    @property
    def area(self) -> float:
        return (self._x2 - self._x1) * (self._y2 - self._y1)

    @property
    def label(self) -> str:
        return self._label

    @property
    def confidence(self) -> float:
        return self._confidence

    def __repr__(self) -> str:
        return f"BoundingBox('{self._label}', conf={self._confidence:.2f}, center={self.center})"
