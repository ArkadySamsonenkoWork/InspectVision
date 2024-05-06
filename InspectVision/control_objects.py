import warnings

import numpy as np
from skimage.metrics import structural_similarity as ssim
import typing as tp

from . import models
from . import gui


class DigitizingModel(tp.Protocol):
    def __init__(self, init_value: float, init_image: np.ndarray):
        pass

    def __call__(self, image: np.ndarray):
        pass


class Similarities:
    @staticmethod
    def cosine_similarity(image_1: np.ndarray, image_2: np.ndarray) -> float:
        """
        :param image_1: first image to calculate similarity.
        :param image_2: second image to calculate similarity.
        :return: similarity of two pictures in terms of cross-correlation.
        """
        similarity = np.sum(image_1 * image_2)
        similarity /= np.sqrt(np.sum(image_1 ** 2) * np.sum(image_2 ** 2))
        return similarity

    @staticmethod
    def structural_similarity(image_1: np.ndarray, image_2: np.ndarray) -> float:
        """
        :param image_1: first image to calculate similarity.
        :param image_2: second image to calculate similarity.
        :return: similarity of two pictures in terms of structure.
        """
        similarity = ssim(image_1, image_2, multichannel=True)
        return similarity


class ControlObject:
    CONV_STEPS = 8
    def __init__(self, coordinates: tuple[int, int, int, int], frame: np.ndarray, init_value: float,
                 name: str, gui_type: gui.WidgetType,
                 weights_similarity: tuple[float, float] = (0.5, 0.5), min_similarity: float=0.7,
                 delta_pixel: int=1, eps: float = 1e-2) -> None:
        """
        :param coordinates: square coordinates of an object
        :param frame: the picture from the camera. It has shape (height,width, channels). And values are float (0, 1) in RGB format by default
        :param init_value: init value og the object. For digital sensor it is number
        :param name: the name of the object that will be shown in output
        :param weights_similarity: the similarities weights:
        two numbers for cross-correlation and structural similarities
        :param min_similarity: minimum acceptable similarity of the first sensor image to all subsequent images.
        This parameter controls the acceptable shift of camera
        :param delta_pixel: the pixel step for update coordinates
        """
        self.init_coordinates = coordinates
        self.current_coordinates = coordinates
        self.init_value = init_value
        self.delta_pixel = delta_pixel
        self.delta_pixel = delta_pixel

        self.weights_similarity = weights_similarity
        self.min_similarity = min_similarity
        self.init_image = self._get_init_image(frame)

        self.current_similarity = 1.0
        self.model = self._init_model()
        self.previous_image = self.init_image # To avoid the model work for each frame
        self.current_value: None | float = None
        self.eps = eps

        self.__name = name
        self.__gui_type = gui_type

    @property
    def gui_type(self):
        return self.__gui_type

    @property
    def name(self):
        return self.__name

    def _init_model(self):
        raise NotImplementedError

    def _check_gui_type(self) -> None:
        """
        Checker of gui_type that you used
        :return:
        """
        pass

    def _get_init_image(self, frame: np.ndarray) -> np.ndarray:
        x1 = self.init_coordinates[0]
        y1 = self.init_coordinates[1]
        x2 = self.init_coordinates[2]
        y2 = self.init_coordinates[3]
        image = frame[y1: y1 + y2, x1: x1 + x2]
        return image

    def _get_similarity(self, image: np.ndarray) -> float:
        cross_correlation = Similarities.cosine_similarity(image, self.init_image)
        structural = Similarities.structural_similarity(image, self.init_image)
        similarity = cross_correlation * self.weights_similarity[0] + structural * self.weights_similarity[1]
        return similarity

    def update_similarity(self, frame: np.ndarray) -> None:
        """
        Updates similarity but doesn't change the coordinates
        :param frame: the picture from the camera. Has shape (height,width, channels)
        :return:
        """
        x1 = self.current_coordinates[0]
        y1 = self.current_coordinates[1]
        x2 = self.current_coordinates[2]
        y2 = self.current_coordinates[3]
        image = frame[y1: y1 + y2, x1: x1 + x2]
        self.current_similarity = self._get_similarity(image)

    def get_current_image(self, frame: np.ndarray) -> np.ndarray:
        """
        :param frame: the picture from the camera. Has shape (height,width, channels)
        :return: Current image of the object relatively to current coordinates
        """
        x1 = self.current_coordinates[0]
        y1 = self.current_coordinates[1]
        x2 = self.current_coordinates[2]
        y2 = self.current_coordinates[3]
        image = frame[y1: y1 + y2, x1: x1 + x2]
        return image

    def update_coordinates(self, frame: np.ndarray) -> None:
        """
        Update coordinates of given object. It can be useful if the view was shifted.
        :param frame: the picture from the camera (height,width, channels)
        :return:None
        """
        x1 = self.current_coordinates[0]
        y1 = self.current_coordinates[1]
        x2 = self.current_coordinates[2]
        y2 = self.current_coordinates[3]
        old_image = frame[y1: y1 + y2, x1: x1 + x2]
        current_similarity = self._get_similarity(old_image)
        x_shifts = [2, 2, 0, -2, -2, -2, 0, 2]
        y_shifts = [0, 2, 2, 2, 0, -2, -2, -2]
        similarities = []
        for step in range(self.CONV_STEPS):
            x1_shifted = x1 + x_shifts[step]
            y1_shifted = y1 + y_shifts[step]
            x2_shifted = x2
            y2_shifted = y2
            new_image = frame[y1_shifted: y1_shifted + y2_shifted, x1_shifted: x1_shifted + x2_shifted]
            similarity = self._get_similarity(new_image)
            similarities.append(similarity)
        similarity_index_max = np.argmax(similarities)
        similarity_max = similarities[similarity_index_max]
        if similarity_max > current_similarity:
            x1_shifted = x1 + x_shifts[similarity_index_max]
            y1_shifted = y1 + y_shifts[similarity_index_max]
            x2_shifted = x2
            y2_shifted = y2
            self.current_coordinates = (x1_shifted, y1_shifted, x2_shifted, y2_shifted)
        self.current_similarity = max(similarity_max, current_similarity)

    def _get_value_flag(self, image):
        flag_value = (self.current_value is None)
        flag_image = np.any(abs(self.previous_image - image) >= self.eps)
        return flag_value or flag_image

    def get_value(self, frame):
        """
        :param frame:
        :return:
        """
        image = self.get_current_image(frame)
        if self._get_value_flag(image):
            value = self.model(image)
        else:
            value = self.current_value
        return value


class Bulb(ControlObject):
    def _init_model(self):
        base_model = models.BulbModel(self.init_value, self.init_image)
        return base_model

    def check_gui_type(self):
        if self.gui_type is not gui.WidgetType.Binary:
            warnings.warn("Git type for bulb must be Binary")

class LedDigits(ControlObject):
    def _init_model(self):
        base_model = models.LedNumbersModel(self.init_value, self.init_image)
        return base_model