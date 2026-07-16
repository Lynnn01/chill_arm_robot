import time
from react_agent.tools import BaseTool, register_tool
from tools import mc

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
