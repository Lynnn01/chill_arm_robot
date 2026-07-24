import os
import sys

# Suppress all background process warnings including multiprocessing leaked semaphores
os.environ["PYTHONWARNINGS"] = "ignore"

# Force PyTorch to use CPU on Jetson to prevent CUDA driver mismatch Segfaults
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

# Monkey-patch torch.cuda to prevent any broken driver queries
try:
    import torch
    torch.cuda.is_available = lambda: False
    torch.cuda.device_count = lambda: 0
    torch.cuda.get_device_name = lambda *args: "CPU"
    if hasattr(torch.backends, 'cudnn'):
        torch.backends.cudnn.is_available = lambda: False
except ImportError:
    pass

# Ensure the root directory is in the sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.gui import start_gui

if __name__ == "__main__":
    start_gui()
    