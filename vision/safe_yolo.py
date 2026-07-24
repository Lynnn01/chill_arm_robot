import os
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"  # Disable CUDA completely at OS level before torch loads

import torch

# Aggressively patch underlying C functions to prevent ANY internal PyTorch calls from hitting the broken driver
if hasattr(torch, '_C'):
    torch._C._cuda_getDeviceCount = lambda: 0
    torch._C._cuda_isDriverSufficient = lambda: False

torch.cuda.is_available = lambda: False
torch.cuda.device_count = lambda: 0
torch.cuda.get_device_name = lambda *args: "CPU"
if hasattr(torch.backends, 'cudnn'):
    torch.backends.cudnn.is_available = lambda: False

from ultralytics import YOLO
