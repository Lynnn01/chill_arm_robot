import time
import json
from PIL import Image
import api
from react_agent.tools import BaseTool, register_tool
from tools import mc
import init
import eyeonhand

@register_tool('grab_object')
class GrabObject(BaseTool):
    description = 'Uses computer vision to detect and grab the specified object from the workspace.'
    parameters = [
        {
            'name': 'object_name',
            'type': 'string',
            'description': 'The descriptive name of the object to grab (e.g., "red block", "blue cube").',
            'required': True
        }
    ]

    def call(self, object_name, **kwargs):
        init.BotInit(mc)

        init.GetImage()

        width, height = Image.open('captured_image.jpg').size
        positions = api.QwenVLRequest("a " + object_name, "captured_image.jpg").get("coordinates", [])
        print(positions)

        with open("config.json", "r", encoding="utf-8") as config_file:
            config_data = json.load(config_file)

        x_offset = config_data.get("x", 0)
        y_offset = config_data.get("y", 0)
        z_offset = config_data.get("z", 0)

        # Process only the first coordinate in positions
        if positions:
            position = positions[0]
            # Calculate center point coordinates
            center_x = (position['x1'] + position['x2']) / 2
            center_y = (position['y1'] + position['y2']) / 2
            target_coord = (center_x / 1000 * width, center_y / 1000 * height)
            robot_coord = eyeonhand.pixel_to_arm(target_coord)
            print("Pixel coordinates {} correspond to robot arm coordinates {}".format(target_coord, robot_coord))
            robot_coord[0]=robot_coord[0]+x_offset
            robot_coord[1]=robot_coord[1]+y_offset
            if robot_coord[0] >210:
                robot_coord[0]=robot_coord[0]-5
            z = 120 + z_offset


            init.open_gripper()
            mc.send_coords([robot_coord[0], robot_coord[1], 200, -173, 0, -45], 40)
            time.sleep(5)
            mc.send_coords([robot_coord[0], robot_coord[1], z, -173, 0, -45], 40)
            time.sleep(5)
            init.close_gripper()

            mc.send_coords([robot_coord[0], robot_coord[1], 200, -173, 0, -45], 20)
            time.sleep(3)
            mc.send_angles([0, 0, 0, 0, 0, -45], 40)
        else:
            print("No position data found")
            return None 

        return robot_coord
