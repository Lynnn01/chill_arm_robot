import torch

# Monkey-patch to prevent CUDA driver Segfault on Jetson
torch.cuda.is_available = lambda: False
torch.cuda.device_count = lambda: 0
torch.cuda.get_device_name = lambda *args: "CPU"
if hasattr(torch.backends, 'cudnn'):
    torch.backends.cudnn.is_available = lambda: False

from ultralytics import YOLO
