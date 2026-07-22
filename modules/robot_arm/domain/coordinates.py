"""
modules/robot_arm/domain/coordinates.py
Domain Layer: Value Objects & Domain Rules for Robot Arm Coordinates
Zero Dependencies on External Frameworks / Hardware SDKs.
"""

import math
import armconfig

class TargetCoordinate:
    """Value Object representing 3D Arm Target Coordinates (X, Y, Z). Immutable."""
    def __init__(self, x: float, y: float, z: float):
        self._x = self._clamp_xy(float(x))
        self._y = self._clamp_xy(float(y))
        self._z = self._clamp_z(float(z))
        self._apply_base_radius_safety()

    @property
    def x(self) -> float:
        return self._x

    @property
    def y(self) -> float:
        return self._y

    @property
    def z(self) -> float:
        return self._z

    def to_list(self) -> list[float]:
        return [self._x, self._y, self._z]

    def _clamp_xy(self, val: float) -> float:
        return max(armconfig.COORD_XY_MIN, min(armconfig.COORD_XY_MAX, val))

    def _clamp_z(self, val: float) -> float:
        return max(armconfig.COORD_Z_MIN, min(armconfig.COORD_Z_MAX, val))

    def _apply_base_radius_safety(self):
        """Prevents hitting robot base if Z is low."""
        if self._z < 100:
            radius = math.sqrt(self._x**2 + self._y**2)
            if radius < armconfig.GRAB_MIN_RADIUS:
                if radius > 0:
                    scale = armconfig.GRAB_MIN_RADIUS / radius
                    self._x = self._x * scale
                    self._y = self._y * scale
                else:
                    self._x = float(armconfig.GRAB_MIN_RADIUS)
                    self._y = 0.0

    def __repr__(self) -> str:
        return f"TargetCoordinate(X={self._x:.2f}, Y={self._y:.2f}, Z={self._z:.2f})"

class AngleSet:
    """Value Object representing Joint Angles [J1..J6]."""
    def __init__(self, angles: list[float]):
        if len(angles) != 6:
            raise ValueError("AngleSet must contain exactly 6 joint angles.")
        self._angles = [float(a) for a in angles]

    @property
    def angles(self) -> list[float]:
        return list(self._angles)

    def to_list(self) -> list[float]:
        return list(self._angles)

    def __repr__(self) -> str:
        return f"AngleSet({self._angles})"
