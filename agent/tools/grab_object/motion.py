import time
import armconfig
from hardware import init
from hardware.init import mc
from agent.tools.shares.motion_sequence import safe_lift, safe_travel_xy, safe_descend, return_home
from agent.tools.shares.coord_transform import clamp_xy, clamp_radius
from agent.tools.shares.config_loader import load_offsets

def execute_grab(object_name: str, coord: list) -> str:
    """ลำดับการเคลื่อนไหวทั้งหมดสำหรับหยิบ"""
    init.BotInit(mc)
    
    cfg = load_offsets()
    z = armconfig.GRAB_BASE_HEIGHT + cfg["z"]

    coord = clamp_xy(coord)
    coord = clamp_radius(coord, z)

    init.open_gripper()
    
    current = mc.safe_get_coords()
    safe_lift(current)
    xy_target = safe_travel_xy(coord[0], coord[1], armconfig.WRIST_DOWN)
    safe_descend(coord[0], coord[1], z, armconfig.WRIST_DOWN)

    init.close_gripper()
    time.sleep(1) # wait for gripper to finish closing
    
    init.current_held_object = object_name
    init.known_objects[object_name] = "in gripper"

    mc.send_coords(xy_target + armconfig.WRIST_DOWN, armconfig.SPEED_LIFT)
    mc.wait_for_arrival(xy_target, mode="coords")
    return_home()

    return f"Successfully grabbed {object_name} at coordinates {coord}"
