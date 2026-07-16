import time
import base64
import json
from PIL import Image
import api
from react_agent.tools import BaseTool, register_tool
from pymycobot.mycobot import MyCobot
from pymycobot.genre import Angle
import numpy as np
from pymycobot import PI_PORT, PI_BAUD  # When using the Raspberry Pi version of MyCobot, these two variables can be referenced to initialize MyCobot
import init
import cv2
import eyeonhand

mc = MyCobot('/dev/ttyUSB0', 1000000)

init.BotInit(mc)
#init.GetImage()

def adjust_gamma(image, gamma=1.0):
    inv_gamma = 1.0 / gamma
    table = np.array([((i / 255.0) ** inv_gamma) * 255 for i in np.arange(0, 256)]).astype("uint8")
    return cv2.LUT(image, table)

@register_tool('move_to')
class MoveTo(BaseTool):
    description = 'This f unction arranges multiple objects into a specific pattern within a designated area after calling function grab_object. You should generate the target_coord parameter dynamically using Python code, and ensure the arrangement follows the given constraints.'
    parameters = [
        {
            'name': 'target_coord',
            'type': 'list',
            'example':'[int,int] ',
            'description':'The target coordinate of the object.The number of it should be the same as object_number. x coordinate should range from -70 to 140, y coordinate should range from 150 to 280. When using this function, you have to generate Python code to get the correct coordinate and I will execute the code for you. The distance between two points should not be less than 50.',
            'get_from_code':True,
            'required':True
        },
        {
            'name': 'target_height',
            'type': 'int',
            'example': '110',
            'description': 'Defines the height at which the object is released. Typically must set all objects to 110. Only if the instruction specifies that objects should be stacked, the height must starts at 110 for the first object and increases by 20 for each subsequent object (e.g., 110 for the first one, 130 for the second, and so on).',
            'first_height':'must be 110',
            'get_from_code': False,
            'required': True
        }
    ]

    def call(self, target_coord, target_height,**kwargs):
        width, height = Image.open("captured_image.jpg").size

        # Move the object to the target position
        target_robot_coord = target_coord
        print("*************")
        print(target_robot_coord)

        time.sleep(3)

        mc.send_coords([target_robot_coord[0], target_robot_coord[1], 180, -175, 0, -45], 40)
        time.sleep(3)

        mc.send_coords([target_robot_coord[0], target_robot_coord[1], target_height, -175, 0, -45], 40)
        time.sleep(3)
        init.open_gripper()
        time.sleep(1)

        mc.send_coords([target_robot_coord[0], target_robot_coord[1], 200, -175, 0, -45], 40)
        time.sleep(3)
        mc.send_angles([0, 0, 0, 0, 0, -45], 40)
        time.sleep(1)

        print("Objects arranged successfully")
        return "Objects arranged successfully."




@register_tool('grab_object')
class GrabObject(BaseTool):
    description = 'This function detects the position of a specified object and performs a grabbing action to retrieve the object. '
    parameters = [
        {
            'name': 'object_name',
            'type': 'string',
            'description': 'The name of the object to be detected and grabbed. ',
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

        return robot_coord

@register_tool('move_around')
class MoveAround(BaseTool):
    description = 'This function makes the robotic arm perform a sequence of movements to look around the environment. Useful for scanning an area or demonstrating range of motion.'
    parameters = [
        {
            'name': 'speed',
            'type': 'int',
            'example': '40',
            'description': 'The speed of the movement, ranging from 10 to 100. Default is 40.',
            'required': False
        }
    ]

    def call(self, speed=40, **kwargs):
        print(f"Executing move around sequence at speed {speed}...")
        
        # 1. Move to default/center position
        mc.send_angles([0, 0, 0, 0, 0, -45], speed)
        time.sleep(3)
        
        # 2. Pan Left
        mc.send_angles([60, 0, 0, 0, 0, -45], speed)
        time.sleep(3)
        
        # 3. Pan Right (Sweep across)
        mc.send_angles([-60, 0, 0, 0, 0, -45], speed)
        time.sleep(4)
        
        # 4. Look Up slightly (adjusting joint 2 and 3)
        mc.send_angles([0, -30, -30, 0, 0, -45], speed)
        time.sleep(3)
        
        # 5. Return to default/center position
        mc.send_angles([0, 0, 0, 0, 0, -45], speed)
        time.sleep(3)
        
        print("Move around sequence completed.")
        return "Arm successfully moved around the environment."



@register_tool('show_object')
class ShowObject(BaseTool):
    description = 'This function shows the object to user after grabbing it, etc. '
    parameters = [
        {
            'name': 'object_name',
            'type': 'string',
            'description': 'show object name ',
            'required': True
        }
    ]


    def call(self,object_name, **kwargs):

        mc.send_angles([0, 0, 0, 0, 0, -45], 40)
        time.sleep(3)
        mc.send_angles([0, 0, 0, -90, 0, -45], 40)
        time.sleep(3)
        return "success"

