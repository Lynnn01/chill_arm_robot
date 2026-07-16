import time
from PIL import Image
from tools import mc
import init
from agents import function_tool

@function_tool
def move_to(target_coord: list, target_height: int = 110) -> str:
    """
    Moves the currently grabbed object to a specific target coordinate [x, y] and releases it at target_height.
    
    Args:
        target_coord: The target coordinate [x, y] to place the object. For complex patterns, calculate this using Python code first.
        target_height: The height to release the object. Default is 110. For stacking, increase by 20 for each subsequent object.
    """
    width, height = Image.open("captured_image.jpg").size

    # Move the object to the target position
    print("*************")
    print(target_coord)

    time.sleep(3)
    mc.send_coords([target_coord[0], target_coord[1], 180, -175, 0, -45], 40)
    time.sleep(3)

    mc.send_coords([target_coord[0], target_coord[1], target_height, -175, 0, -45], 40)
    time.sleep(3)
    init.open_gripper()
    time.sleep(1)

    mc.send_coords([target_coord[0], target_coord[1], 200, -175, 0, -45], 40)
    time.sleep(3)
    mc.send_angles([0, 0, 0, 0, 0, -45], 40)
    time.sleep(1)

    print("Objects arranged successfully")
    return "Objects arranged successfully."
