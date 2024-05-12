from collections import OrderedDict
from datetime import datetime

import typing as tp
from pathlib import Path
import time

import cv2
import numpy as np

from . import handlers
from . import gui
from .data_logging import FileLogger
from .data_logging import TelegramApi
from .processing.image_processing import ImageProcessor


class ValueSerializator:
    def __init__(self, control_objects: tp.Iterable[handlers.ControlObject]):
        self.__meta = self._get_meta(control_objects)

    @property
    def meta(self) -> dict[str, gui.WidgetType | None]:
        return self.__meta

    def _get_meta(self, control_objects: tp.Iterable[handlers.ControlObject])\
            -> dict[str, gui.WidgetType | None]:
        """
        :param control_objects: control_objects
        :return: None
        """
        meta = dict()
        for control_object in control_objects:
            if control_object.name in meta:
                raise KeyError("name of objects must be unique")
            meta[control_object.name] = control_object.gui_type
        return meta

    def _get_time(self) -> datetime:
        return datetime.now()

    def gui_out_repr(self, data: dict[str: float]) -> dict[str, tp.Any]:
        gui_output = dict()
        for i, item in enumerate(data.items()):
            name, value = item
            gui_type = self.meta[name]
            gui_name = f"{i+1}) {name}"
            if gui_type is gui.WidgetType.Plot:
                gui_output[gui_name] = (self._get_time(), value)
            else:
                gui_output[gui_name] = value
        return gui_output

    def gui_names(self) -> list[str]:
        out_names = []
        for i, item in enumerate(self.meta.items()):
            name, value = item
            if value is not None:
                gui_name = f"{i+1}) {name}"
                out_names.append(gui_name)
        return out_names

    def gui_names_type(self) -> dict[str, gui.WidgetType | None]:
        name_type = OrderedDict()
        for i, item in enumerate(self.meta.items()):
            name, gui_type = item
            if gui_type is not None:
                gui_name = f"{i+1}) {name}"
                name_type[gui_name] = gui_type
        return name_type

    def logger_out_repr(self, data: dict[str: float]) -> dict[str, tp.Any]:
        result = {"time": self._get_time()}
        result.update(data)
        return result

    def logger_names(self) -> list[str]:
        return ["time"] + list(self.meta.keys())


class UpdateManager:
    def __init__(self, serilizator: ValueSerializator,
                 log_path: None | str | Path, show: bool, telegram_api: TelegramApi | None,
                 update_pos: bool, log_every: int
                 ):
        self.time = time.time()
        self.serilizator = serilizator
        self.log_path = log_path
        self.show = show
        self.update_pos = update_pos
        self.log_every = log_every
        self.telegram_api = telegram_api

        if telegram_api is not None:
            self.telegram_api.run()
        if show:
            self.gui_handler = gui.GuiHandler(serilizator.gui_names_type())
        if self.log_path is not None:
            names = serilizator.logger_names()
            self.file_logger = FileLogger(log_path, names)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.gui_handler.exit()
        self.file_logger.close()

    def _get_delta_time(self) -> float:
        now_time = time.time()
        delta_time = now_time - self.time
        return delta_time

    def log_in_file(self, update_data):
        if self._get_delta_time() >= self.log_every:
            self.file_logger.write_results(update_data)
            self.time = time.time()

    def update(self, frame: np.ndarray, update_data: dict[str, float]) -> None:
        if self.show:
            gui_repr = self.serilizator.gui_out_repr(update_data)
            self.gui_handler.update(frame, gui_repr)
        if self.log_path is not None:
            logging_repr = self.serilizator.logger_out_repr(update_data)
            self.log_in_file(logging_repr)
        if self.telegram_api is not None:
            self.telegram_api.update(update_data)


class Monitor:
    def __init__(self, image_processor: ImageProcessor):
        self.vid = image_processor
        self.init_time = time.time()

    def _update_coordinates(self, control_object: handlers.ControlObject, frame: np.ndarray):
        control_object.update_similarity(frame)
        old_similarity = control_object.current_similarity
        control_object.update_coordinates(frame)
        new_similarity = control_object.current_similarity

        while not np.allclose(old_similarity, new_similarity):
            old_similarity = new_similarity
            control_object.update_coordinates(frame)
            new_similarity = control_object.current_similarity

    def _add_numbers(self, frame: np.ndarray, coordinates: tp.Iterable[tuple[int, int, int, int]],
                    color: tuple[float, float, float] = (1.0, 0, 0), scale: float = 0.7,
                    thickness: int = 1) -> np.ndarray:
        shift_y = 20  # Hyperparameter
        shift_x = 3  # Hyperparameter
        font = cv2.FONT_HERSHEY_COMPLEX  # Hyperparameter
        for i, coordinate in enumerate(coordinates):
            cv2.putText(
                frame, f"{i + 1}", (coordinate[0] + shift_x, coordinate[1] + shift_y),
                font, scale, color, thickness)
        return frame

    def _highlight_boundaries(self, frame: np.ndarray, coordinates: tp.Iterable[tuple[int, int, int, int]],
                             width=2, color: tuple[float, float, float] = (1.0, 0, 0)) -> np.ndarray:
        """
        :param frame: The picture in float (0, 1) with shape (height, width, channels)
        :param coordinates: the coordinates of all objects
        :param width: The width of boundary
        :param color: the color of the boundary in r,g,b normalized (0,1)
        :return: processed frame
        """
        mask = np.zeros_like(frame)
        for coordinate in coordinates:
            x1 = coordinate[0]
            y1 = coordinate[1]
            x2 = coordinate[2]
            y2 = coordinate[3]
            mask[(y1 - width):(y1 + y2 + width), (x1 - width):(x1 + x2 + width)] = 1
            mask[y1:(y1 + y2), x1:(x1 + x2)] = 0
        processed_frame = np.where(mask, color, frame)
        return processed_frame

    def _mark_objects_view(self, frame: np.ndarray, coordinates: tp.Iterable[tuple[int, int, int, int]],
                          alpha: float = 0.5) -> np.ndarray:
        """
        :param frame: The picture in float (0, 1) with shape (height,width, channels)
        :param coordinates: the coordinates of all objects
        :param alpha: Transparency factor
        :return: processed frame
        """
        processed_frame = (frame + alpha) / (1 + alpha)
        mask = np.zeros_like(frame)
        for coordinate in coordinates:
            x1 = coordinate[0]
            y1 = coordinate[1]
            x2 = coordinate[2]
            y2 = coordinate[3]
            mask[y1:(y1 + y2), x1:(x1 + x2)] = 1
        processed_frame = np.where(mask, frame, processed_frame)
        return processed_frame

    def process_view(self, frame: np.ndarray,
                      control_objects: tp.Iterable[handlers.ControlObject]) -> np.ndarray:
        """
        Process the figure adding boundaries for objects, numbers and highlite objects on a picture
        :param frame: The picture in float (0, 1) with shape (height,width, channels) in rgb format
        :param control_objects: The objects that controlled under program
        :return:
        """
        coordinates = [control_object.current_coordinates for control_object in control_objects]

        processed_frame = self._mark_objects_view(frame, coordinates)
        processed_frame = self._highlight_boundaries(processed_frame, coordinates, width=3, color=(1.0, 0, 0))
        processed_frame = self._add_numbers(processed_frame, coordinates)
        return processed_frame

    def process_similarities(self, frame: np.ndarray,
                             control_objects: tp.Iterable[handlers.ControlObject],
                             update_pos: bool) -> None:
        """
        Process the figure adding boundaries for objects, numbers and highlight objects on a picture
        :param frame: The picture in float (0, 1) with shape (height,width, channels)
        :param control_objects: The objects that controlled under program
        :param update_pos: update positions of the objects
        :return:
        """
        for control_object in control_objects:
            if update_pos:
                self._update_coordinates(control_object, frame)
            control_object.update_similarity(frame)
            similarity = control_object.current_similarity
            if similarity < control_object.min_similarity:
                print(1)
                raise RuntimeError(f"similarity for object {control_object.name} is too low {similarity}")

    def collect_object_values(self, frame: np.ndarray,
                               control_objects: tp.Iterable[handlers.ControlObject]):
        values = {}
        for control_object in control_objects:
            values[control_object.name] = control_object.get_value(frame)
        return values

    def _get_values(self, frame: np.ndarray,
                    control_objects: tp.Iterable[handlers.ControlObject]
                    ) -> dict[str, float]:
        update_data = {
            control_object.name: control_object.get_value(frame) for control_object in control_objects}
        return update_data

    def _procces_data(self, control_objects: tp.Iterable[handlers.ControlObject], update_pos: bool
                      ) -> tuple[np.ndarray, dict[str, float]]:
        frame = self.vid.capture_frame()
        self.process_similarities(frame, control_objects, update_pos)
        update_data = self._get_values(frame, control_objects)
        return frame, update_data

    def run_loop(self, control_objects: tp.Iterable[handlers.ControlObject],
                 log_path: None | str | Path=None, show: bool=True, telegram_api: TelegramApi | None=None,
                 update_pos: bool=True, log_every:int=10) -> None:
        """
        :param control_objects: The objects that we try to control
        :param show: Show figures with data
        :param telegram_api: telegram_api
        :param update_pos: update positions of the objects
        :param log_every: log every steps
        :return:
        """
        serilizator = ValueSerializator(control_objects)
        with UpdateManager(serilizator=serilizator,
                           log_path=log_path, show=show, telegram_api=telegram_api,
                           update_pos=update_pos, log_every=log_every) as manager:
            while True:
                frame, update_data = self._procces_data(control_objects, update_pos)
                proccessed_frame = self.process_view(frame=frame, control_objects=control_objects)
                manager.update(proccessed_frame, update_data)

    def release_camera(self):
        self.vid.release()
