import time
from PIL import Image
from react_agent.tools import BaseTool, register_tool
from tools import mc
import init

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
