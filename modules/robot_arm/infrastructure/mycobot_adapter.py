"""
modules/robot_arm/infrastructure/mycobot_adapter.py
Infrastructure Layer: Adapter implementing RobotHardwarePort via hardware.init.mc
"""

from typing import Optional
from hardware.init import mc, open_gripper, close_gripper
from modules.robot_arm.application.ports import RobotHardwarePort

class MyCobotHardwareAdapter(RobotHardwarePort):
    """Adapter bridging application Port calls to PyMyCobot driver instance."""

    def send_coords(self, coords: list[float], speed: int) -> None:
        mc.send_coords(coords, speed)

    def send_angles(self, angles: list[float], speed: int) -> None:
        mc.send_angles(angles, speed)

    def send_angle(self, joint: int, angle: float, speed: int) -> None:
        mc.send_angle(joint, angle, speed)

    def safe_get_coords(self) -> Optional[list[float]]:
        return mc.safe_get_coords()

    def safe_get_angles(self) -> Optional[list[float]]:
        return mc.safe_get_angles()

    def wait_for_arrival(self, target: list[float], mode: str = "coords", timeout: float = 10.0) -> bool:
        return mc.wait_for_arrival(target, mode=mode, timeout=timeout)

    def wait_for_z(self, target_z: float, timeout: float = 10.0) -> bool:
        return mc.wait_for_z(target_z, timeout=timeout)

    def open_gripper(self) -> None:
        open_gripper()

    def close_gripper(self) -> None:
        close_gripper()
