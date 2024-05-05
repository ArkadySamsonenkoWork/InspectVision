import cv2
import numpy as np
import scipy
from skimage.metrics import structural_similarity as ssim
from enum import Enum

from . import models


from abc import ABC, abstractmethod

class ObjectsType(Enum):
    Plot = 0
    Display = 1
    Binary = 2


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

class ControlObject(ABC):
    CONV_STEPS = 8
    def __init__(self, coordinates: tuple[int, int, int, int], frame: np.ndarray, type: ObjectsType,
                 init_value: float | None=None,
                 name: str | None=None,
                 weights_similarity: tuple[float, float] = (0.5, 0.5), min_similarity: float=0.7,
                 delta_pixel: int=1,) -> None:
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
        self.type = type
        self.weights_similarity = weights_similarity
        self.min_similarity = min_similarity
        self.name = name
        self.init_image = self._get_init_image(frame)
        self.current_similarity = 1.0

        self._init_base_model()

    @abstractmethod
    def _init_base_model(self):
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

    def get_object_position(self, frame: np.ndarray):
        """
        Finds the image in the picture that is most similar to the base object
        :param frame: the picture from the camera Has shape (height,width, channels)
        :return: None
        """
        raise NotImplementedError
        channels = frame[0]
        x_size = frame[1] - self.init_image[1] + 1
        y_size = frame[2] - self.init_image[2] + 1
        convs = np.empty(shape=(channels, x_size, y_size))
        support_conv = np.ones_like(self.init_image)
        frame_norm_tot = frame * frame
        frame_norm_convs = np.empty_like(convs)
        for channel in range(channels):
            convs[channel] = scipy.signal.correlate2d(frame, self.init_image, "valid")
            frame_norm_convs[channel] = scipy.signal.correlate2d(frame_norm_tot, support_conv, "valid")
        full_dot_conv = convs.sum(axis=0)
        init_picture_norm = np.linalg.norm(self.init_image)
        similarities_matrix = full_dot_conv / (frame_norm_convs * init_picture_norm)
        accepted_similarities = similarities_matrix >= self.min_similarity
        if accepted_similarities.sum() > 1:
            raise RuntimeError(f"Too many similarities greater than accepted similarity {self.min_similarity}")
        elif accepted_similarities.sum() < 1:
            raise RuntimeError(f"There are no similarities greater than accepted similarity {self.min_similarity}")
        elif accepted_similarities.sum() == 1:
            positions = np.where(accepted_similarities == True)
            x, y = positions
            x, y = x.item(), y.item()
            x1 = x
            y1 = y
            x2 = x + self.init_image[1]
            y2 = y + self.init_image[2]
            self.current_coordinates = (x1, y1, x2, y2)
            self.current_similarity = max(similarities_matrix)

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
        for step in range(ControlObject.CONV_STEPS):
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

    def get_value(self, frame):
        image = self.get_current_image(frame)
        value = self.base_model(image)
        return value


class Bulb(ControlObject):
    def _init_base_model(self):
        self.base_model = models.BulbModel(self.init_value, self.init_image)

class LedDigits(ControlObject):
    def _init_base_model(self):
        self.base_model = models.LedNumbersModel(self.init_value, self.init_image)