"""
modules/robot_arm/application/ports.py
Application Layer: Ports (Interfaces) for Robot Hardware Operations
Decouples Application Logic from PyMyCobot / Hardware Drivers.
"""

from typing import Protocol, Optional
from modules.robot_arm.domain.coordinates import TargetCoordinate, AngleSet

class RobotHardwarePort(Protocol):
    """Hexagonal Port Interface for Robotic Arm Control."""
    
    def send_coords(self, coords: list[float], speed: int) -> None:
        ...

    def send_angles(self, angles: list[float], speed: int) -> None:
        ...

    def send_angle(self, joint: int, angle: float, speed: int) -> None:
        ...

    def safe_get_coords(self) -> Optional[list[float]]:
        ...

    def safe_get_angles(self) -> Optional[list[float]]:
        ...

    def wait_for_arrival(self, target: list[float], mode: str = "coords", timeout: float = 10.0) -> bool:
        ...

    def wait_for_z(self, target_z: float, timeout: float = 10.0) -> bool:
        ...

    def open_gripper(self) -> None:
        ...

    def close_gripper(self) -> None:
        ...
