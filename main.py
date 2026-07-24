import os
import sys

# Suppress annoying multiprocessing leaked semaphore warnings on Linux
import warnings
import multiprocessing.resource_tracker
# Monkey-patch warnings.warn inside the resource_tracker module so it never prints anything
multiprocessing.resource_tracker.warnings.warn = lambda *args, **kwargs: None

# Ensure the root directory is in the sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.gui import start_gui

if __name__ == "__main__":
    start_gui()
    