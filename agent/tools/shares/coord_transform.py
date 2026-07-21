import math
import armconfig

def pixel_center(position: dict) -> tuple:
    """แปลง bounding box เป็น center pixel (normalized 0-1000)"""
    cx = (position["x1"] + position["x2"]) / 2
    cy = (position["y1"] + position["y2"]) / 2
    return cx, cy

def apply_rotation(coord: list, j1_deg: float) -> list:
    """หมุน local arm coord กลับมาเป็น world coord ตาม J1 angle"""
    theta = math.radians(j1_deg)
    x_w = coord[0] * math.cos(theta) - coord[1] * math.sin(theta)
    y_w = coord[0] * math.sin(theta) + coord[1] * math.cos(theta)
    return [x_w, y_w]

def clamp_xy(coord: list) -> list:
    """จำกัดพิกัด XY ให้อยู่ในขอบเขตปลอดภัย"""
    return [
        max(armconfig.COORD_XY_MIN, min(armconfig.COORD_XY_MAX, coord[0])),
        max(armconfig.COORD_XY_MIN, min(armconfig.COORD_XY_MAX, coord[1])),
    ]

def clamp_radius(coord: list, z: float) -> list:
    """ป้องกันหยิบใกล้ฐานเกินไป"""
    if z >= 100:
        return coord
    radius = math.sqrt(coord[0]**2 + coord[1]**2)
    if radius < armconfig.GRAB_MIN_RADIUS and radius > 0:
        scale = armconfig.GRAB_MIN_RADIUS / radius
        return [coord[0] * scale, coord[1] * scale]
    elif radius == 0:
        return [armconfig.GRAB_MIN_RADIUS, 0]
    return coord
