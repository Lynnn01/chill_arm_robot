import time
import json
from PIL import Image
from vision import api
from hardware.init import mc
from hardware import init
from vision import eyeonhand
from agents import function_tool

@function_tool
def grab_object(object_name: str, target_coord: list = None) -> list:
    """
    Uses computer vision to detect and grab the specified object from the workspace.
    If target_coord is provided, it skips vision and grabs directly from that location.
    
    Args:
        object_name: The descriptive name of the object to grab (e.g., "red block", "blue cube").
        target_coord: Optional [x, y] coordinates to grab from. If provided, vision is skipped.
    """
    init.BotInit(mc)
    
    with open("config.json", "r", encoding="utf-8") as config_file:
        config_data = json.load(config_file)

    x_offset = config_data.get("x", 0)
    y_offset = config_data.get("y", 0)
    z_offset = config_data.get("z", 0)
    z = 120 + z_offset

    if target_coord and len(target_coord) >= 2:
        print(f"Skipping vision, using provided coordinates: {target_coord}")
        robot_coord = [float(target_coord[0]), float(target_coord[1])]
    else:
        init.GetImage()
        width, height = Image.open('captured_image.jpg').size
        positions = api.QwenVLRequest("a " + object_name, "captured_image.jpg").get("coordinates", [])
        print(positions)

        if positions:
            position = positions[0]
            # Calculate center point coordinates
            center_x = (position['x1'] + position['x2']) / 2
            center_y = (position['y1'] + position['y2']) / 2
            target_pixel = (center_x / 1000 * width, center_y / 1000 * height)
            robot_coord = eyeonhand.pixel_to_arm(target_pixel)
            print("Pixel coordinates {} correspond to robot arm coordinates {}".format(target_pixel, robot_coord))
            robot_coord[0] = robot_coord[0] + x_offset
            robot_coord[1] = robot_coord[1] + y_offset
            if robot_coord[0] > 210:
                robot_coord[0] = robot_coord[0] - 5
        else:
            print("No position data found")
            return []

    # Safety clamps for grasping
    robot_coord[0] = max(140.0, min(280.0, float(robot_coord[0])))
    robot_coord[1] = max(-100.0, min(100.0, float(robot_coord[1])))

    init.open_gripper()
    mc.send_coords([robot_coord[0], robot_coord[1], 200, -173, 0, -45], 40)
    time.sleep(5)
    mc.send_coords([robot_coord[0], robot_coord[1], z, -173, 0, -45], 40)
    time.sleep(5)
    init.close_gripper()

    mc.send_coords([robot_coord[0], robot_coord[1], 200, -173, 0, -45], 20)
    time.sleep(3)
    mc.send_angles([0, 0, 0, 0, 0, -45], 40)

    return robot_coord
