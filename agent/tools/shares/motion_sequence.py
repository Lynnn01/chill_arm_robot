import armconfig
from hardware.init import mc

def safe_lift(current_coords: list):
    """ยกแขนขึ้นตรงๆ ก่อนเคลื่อนย้าย"""
    if current_coords and len(current_coords) >= 3:
        target = [current_coords[0], current_coords[1], armconfig.Z_SAFE_TRAVEL]
        mc.send_coords(target + armconfig.WRIST_DOWN, armconfig.SPEED_GRAB)
        mc.wait_for_arrival(target, mode="coords")

def safe_travel_xy(x: float, y: float, wrist=None):
    """เคลื่อนย้าย XY ที่ความสูงปลอดภัย"""
    wrist = wrist or armconfig.WRIST_PLACE
    target = [x, y, armconfig.Z_SAFE_TRAVEL]
    mc.send_coords(target + wrist, armconfig.SPEED_GRAB)
    mc.wait_for_arrival(target, mode="coords")
    return target

def safe_descend(x: float, y: float, z: float, wrist=None):
    """ลงไปที่ความสูง z"""
    wrist = wrist or armconfig.WRIST_DOWN
    target = [x, y, z]
    mc.send_coords(target + wrist, armconfig.SPEED_GRAB)
    mc.wait_for_arrival(target, mode="coords")

def return_home():
    """กลับท่า Home"""
    mc.send_angles(armconfig.POSE_HOME, armconfig.SPEED_GRAB)
    mc.wait_for_arrival(armconfig.POSE_HOME, mode="angles")
