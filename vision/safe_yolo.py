import os
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"  # Disable CUDA completely at OS level before torch loads

import torch
torch.cuda.is_available = lambda: False
torch.cuda.device_count = lambda: 0
torch.cuda.get_device_name = lambda *args: "CPU"
if hasattr(torch.backends, 'cudnn'):
    torch.backends.cudnn.is_available = lambda: False

from ultralytics import YOLO
