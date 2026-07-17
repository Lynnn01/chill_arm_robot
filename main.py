import os
import sys

# Ensure the root directory is in the sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.gui import start_gui

if __name__ == "__main__":
    start_gui()
