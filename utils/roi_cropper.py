"""
ROI region cropping tool
Used to crop multiple regions of interest from an image based on bounding box coordinates
"""
import cv2
import numpy as np
from PIL import Image
import logging

logger = logging.getLogger(__name__)


class ROICropper:
    """ROI Region Cropper"""

    def __init__(self, padding=10, min_size=50):
        """
        Args:
            padding: ROI boundary expansion pixels (to avoid cropping too tightly)
            min_size: Minimum ROI size, ROIs smaller than this will be skipped
        """
        self.padding = padding
        self.min_size = min_size

    def crop_rois(self, image_path, positions):
        """
        Crop multiple ROI regions from the image

        Args:
            image_path: Original image path
            positions: List of coordinates returned by Qwen-VL
                Format: [{'x1': int, 'y1': int, 'x2': int, 'y2': int}, ...]
                Note: x1, y1, x2, y2 are relative coordinates (0-1000)

        Returns:
            List[Tuple[PIL.Image, dict]]: List of (ROI image, coordinate information)
                Coordinate information includes:
                - 'index': ROI index
                - 'bbox': (x1, y1, x2, y2) Absolute pixel coordinates
                - 'center': (center_x, center_y) Center point pixel coordinates
        """
        # Read image
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Cannot read image: {image_path}")

        height, width = image.shape[:2]
        roi_images = []

        for idx, position in enumerate(positions):
            # 1. Convert relative coordinates to Absolute pixel coordinates
            x1 = int(position['x1'] / 1000 * width)
            y1 = int(position['y1'] / 1000 * height)
            x2 = int(position['x2'] / 1000 * width)
            y2 = int(position['y2'] / 1000 * height)

            # 2. Apply boundary expansion
            x1 = max(0, x1 - self.padding)
            y1 = max(0, y1 - self.padding)
            x2 = min(width, x2 + self.padding)
            y2 = min(height, y2 + self.padding)

            # 3. Check minimum size
            if (x2 - x1) < self.min_size or (y2 - y1) < self.min_size:
                logger.warning(f"ROI {idx} Size too small ({x2-x1}x{y2-y1}), Skipping")
                continue

            # 4. Crop ROI
            roi = image[y1:y2, x1:x2]

            # 5. Convert to PIL Image
            roi_pil = Image.fromarray(cv2.cvtColor(roi, cv2.COLOR_BGR2RGB))

            # 6. Calculate center point
            center_x = (x1 + x2) // 2
            center_y = (y1 + y2) // 2

            roi_images.append((roi_pil, {
                'index': idx,
                'bbox': (x1, y1, x2, y2),
                'center': (center_x, center_y)
            }))

        logger.info(f"Successfully cropped {len(roi_images)} ROI regions")
        return roi_images
