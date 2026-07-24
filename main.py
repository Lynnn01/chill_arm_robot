import os
import sys
import faulthandler
from dotenv import load_dotenv

faulthandler.enable()  # Catch Segmentation Faults and print the exact line of code!
load_dotenv()  # Load .env BEFORE anything else gets imported

# Suppress all background process warnings including multiprocessing leaked semaphores
os.environ["PYTHONWARNINGS"] = "ignore"

# Force PyTorch to use CPU on Jetson to prevent CUDA driver mismatch Segfaults
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

# Ensure the root directory is in the sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.gui import start_gui

if __name__ == "__main__":
    start_gui()
    