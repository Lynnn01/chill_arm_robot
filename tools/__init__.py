import os
from pymycobot.mycobot import MyCobot
import init

mycobot_port = os.getenv("MYCOBOT_PORT", "/dev/ttyUSB0")
mycobot_baud = int(os.getenv("MYCOBOT_BAUD", "1000000"))
mc = MyCobot(mycobot_port, mycobot_baud)

init.BotInit(mc)

from .move_to import move_to
from .grab_object import grab_object
from .move_around import move_around
from .show_object import show_object
from .execute_code import execute_python_code

agent_tools = [move_to, grab_object, move_around, show_object, execute_python_code]
