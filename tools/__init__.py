import os
from pymycobot.mycobot import MyCobot
import init

mycobot_port = os.getenv("MYCOBOT_PORT", "/dev/ttyUSB0")
mycobot_baud = int(os.getenv("MYCOBOT_BAUD", "1000000"))
mc = MyCobot(mycobot_port, mycobot_baud)

init.BotInit(mc)

from .move_to import MoveTo
from .grab_object import GrabObject
from .move_around import MoveAround
from .show_object import ShowObject
