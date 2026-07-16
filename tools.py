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
import os
import cv2
import eyeonhand

mycobot_port = os.getenv("MYCOBOT_PORT", "/dev/ttyUSB0")
mycobot_baud = int(os.getenv("MYCOBOT_BAUD", "1000000"))
mc = MyCobot(mycobot_port, mycobot_baud)

init.BotInit(mc)
#init.GetImage()

@register_tool('move_to')
class MoveTo(BaseTool):
    description = 'Moves the currently grabbed object to a specific target coordinate [x, y] and releases it at target_height.'
    parameters = [
        {
            'name': 'target_coord',
            'type': 'list',
            'example':'[int,int] ',
            'description':'The target coordinate [x, y] to place the object. For complex patterns, calculate this using Python code first.',
            'get_from_code':True,
            'required':True
        },
        {
            'name': 'target_height',
            'type': 'int',
            'example': '110',
            'description': 'The height to release the object. Default is 110. For stacking, increase by 20 for each subsequent object.',
            'first_height':'must be 110',
            'get_from_code': False,
            'required': True
        }
    ]

    def call(self, target_coord, target_height,**kwargs):
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

@register_tool('move_around')
class MoveAround(BaseTool):
    description = 'Performs a scanning animation to look around the environment.'
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
    description = 'Lifts the arm to present the currently grabbed object to the user or camera.'
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

