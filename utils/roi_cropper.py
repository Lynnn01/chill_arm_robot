"""
ROI 区域裁剪工具
用于从图像中根据边界框坐标裁剪多个感兴趣区域
"""
import cv2
import numpy as np
from PIL import Image
import logging

logger = logging.getLogger(__name__)


class ROICropper:
    """ROI 区域裁剪器"""

    def __init__(self, padding=10, min_size=50):
        """
        Args:
            padding: ROI 边界扩充像素（避免裁剪过紧）
            min_size: 最小ROI尺寸，小于此尺寸的ROI会被跳过
        """
        self.padding = padding
        self.min_size = min_size

    def crop_rois(self, image_path, positions):
        """
        从图像中裁剪多个 ROI 区域

        Args:
            image_path: 原始图像路径
            positions: Qwen-VL 返回的坐标列表
                格式: [{'x1': int, 'y1': int, 'x2': int, 'y2': int}, ...]
                注意：x1,y1,x2,y2 是相对坐标（0-1000）

        Returns:
            List[Tuple[PIL.Image, dict]]: (ROI图像, 坐标信息) 的列表
                坐标信息包含：
                - 'index': ROI索引
                - 'bbox': (x1, y1, x2, y2) 绝对像素坐标
                - 'center': (center_x, center_y) 中心点像素坐标
        """
        # 读取图像
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"无法读取图像: {image_path}")

        height, width = image.shape[:2]
        roi_images = []

        for idx, position in enumerate(positions):
            # 1. 将相对坐标转换为绝对像素坐标
            x1 = int(position['x1'] / 1000 * width)
            y1 = int(position['y1'] / 1000 * height)
            x2 = int(position['x2'] / 1000 * width)
            y2 = int(position['y2'] / 1000 * height)

            # 2. 应用边界扩充
            x1 = max(0, x1 - self.padding)
            y1 = max(0, y1 - self.padding)
            x2 = min(width, x2 + self.padding)
            y2 = min(height, y2 + self.padding)

            # 3. 检查最小尺寸
            if (x2 - x1) < self.min_size or (y2 - y1) < self.min_size:
                logger.warning(f"ROI {idx} 尺寸过小 ({x2-x1}x{y2-y1})，跳过")
                continue

            # 4. 裁剪 ROI
            roi = image[y1:y2, x1:x2]

            # 5. 转换为 PIL Image
            roi_pil = Image.fromarray(cv2.cvtColor(roi, cv2.COLOR_BGR2RGB))

            # 6. 计算中心点
            center_x = (x1 + x2) // 2
            center_y = (y1 + y2) // 2

            roi_images.append((roi_pil, {
                'index': idx,
                'bbox': (x1, y1, x2, y2),
                'center': (center_x, center_y)
            }))

        logger.info(f"成功裁剪 {len(roi_images)} 个 ROI 区域")
        return roi_images
