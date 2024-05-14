from abc import ABC, abstractmethod
import typing as tp
from matplotlib import pyplot as plt

import numpy as np

from . import digits_detector


class BaseProcessModel:
    def __init__(self, init_value: float, init_image: np.ndarray):
        self.init_value = init_value
        self.init_image = init_image

    @abstractmethod
    def forward(self, image: np.ndarray) -> tp.Any:
        """
        :param figure: the image with shape (channels, height, width) in (-0.5, 0.5)
        :return: the value of the object
        """
        pass

    def _init_transforms(self, image: np.ndarray) -> np.ndarray:
        """
        :param image:  the image with shape (height, width, channels) in (0, 1)
        :return: transformed image with shape (channels, height, width) in (-0.5, 0.5)
        """
        transformed_image= image.copy()
        transformed_image = np.moveaxis(transformed_image, -1, 0)
        transformed_image -= 0.5
        return transformed_image

    def __call__(self, image: np.ndarray) -> tp.Any:
        """
        :param image: the image with shape (height, width, channels) in (0, 1)
        :return: the value of the object
        """
        transformed_image = self._init_transforms(image)
        return self.forward(transformed_image)


class BulbModel(BaseProcessModel):
    RED_COEFF = 0.33
    GREEN_COEFF = 0.5
    BLUE_COEFF = 0.16
    def __init__(self, init_value: float, init_image: np.ndarray, max_margin: float=0.2):
        super().__init__(init_value, init_image)
        self.limit_margin = max_margin
        self.init_rel_bright = self._get_rel_bright(
            self._init_transforms(init_image)
        )

    def _get_bright_picture(self, image: np.ndarray):
        return image[0] * BulbModel.RED_COEFF + image[1] * BulbModel.GREEN_COEFF + image[2] * BulbModel.BLUE_COEFF

    def _init_transforms(self, image: np.ndarray) -> np.ndarray:
        """
        :param image:  the image with shape (height, width, channels) in (0, 1)
        :return: transformed image with shape (height, width) in (-0.5, 0.5)
        """
        transformed_image = image.copy()
        transformed_image = np.moveaxis(transformed_image, -1, 0)
        transformed_image = transformed_image - 0.5
        return self._get_bright_picture(transformed_image)

    def _get_rel_bright(self, image: np.ndarray) -> float:
        """
        :param image: the image of the object with shape (width, height) in (-0.5, 0.5)
        :return: the difference between max brightness and min brightness
        """
        return np.max(image) - np.min(image)

    def forward(self, image: np.ndarray):
        """
        :param image: the image of the object with shape (height, width) in (-0.5, 0.5)
        :return: 0 if OFF, 1 if ONN
        """
        current_rel_bright = self._get_rel_bright(image)
        margin = self.init_rel_bright - current_rel_bright
        if self.init_value:
            return margin < self.limit_margin
        else:
            return -margin > self.limit_margin


class LedNumbersModel(BaseProcessModel):
    """
    Models for detection the 7-segments digits. Usually it works fine on any kind of "accurate" digits.
    """
    def __init__(self, init_value: float, init_image: np.ndarray):
        super().__init__(init_value, init_image)
        path = "inspect_vision/models/digits_detector/yolo_digits.onnx"
        self.yolov8_detector = digits_detector.YOLOv8(path, conf_thres=0.2, iou_thres=0.3)

        if self(init_image) != str(init_value):
            warnings.warn("The wrong determination of digits on a picture. Reprocess image")
            # raise RuntimeError("The wrong determination of digits on a picture. Reprocess image")

    def _init_transforms(self, image: np.ndarray, height: int=200) -> np.ndarray:
        """
        :param image:  the image with shape (height, width, channels) in (0, 1)
        :param height:  the height of image for transformation
        :return: transformed image with shape (height, width, channels) in (0, 1)
        """
        transformed_image = (image.copy() * 255).astype(np.uint8)
        return transformed_image

    def forward(self, image: np.ndarray) -> str:
        print(image.shape)
        plt.imshow(image)
        plt.show()
        boxes, _, class_ids = self.yolov8_detector(image)
        positions = [box[0] for box in boxes]
        number = "".join([digits_detector.CLASS_NAMES[class_id] for _, class_id in sorted(zip(positions, class_ids))])
        print(number)
        print(1)
        return number


