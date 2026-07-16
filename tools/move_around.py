import time
from react_agent.tools import BaseTool, register_tool
from tools import mc

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
