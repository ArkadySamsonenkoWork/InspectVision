import typing
from pathlib import Path
import time

import cv2
import numpy as np

from . import control_objects
from .gui import gui_monitor
from .data_logging import FileLogger
from .data_logging import TelegramApi

class UpdateManager:
    def __init__(self, plots_names: list[str], lcds_names: list[str], binaries_names: list[str],
                 log_path: None | str | Path, show: bool, telegram_api: TelegramApi | None,
                 update_pos: bool, log_every: int
                 ):
        self.time = time.time()
        self.plots_names = plots_names
        self.binaries_names = binaries_names
        self.lcds_names = lcds_names
        self.log_path = log_path
        self.show = show
        self.update_pos = update_pos
        self.log_every = log_every
        self.telegram_api = telegram_api

        if telegram_api is not None:
            self.telegram_api.run()
        if show:
            self.gui_handler = gui_monitor.gui_control.GuiHandler(plots_names, lcds_names, binaries_names)
        if self.log_path is not None:
            names = plots_names+binaries_names+lcds_names
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

    def log_in_file(self, plots_data, lsds_data, binaries_data):
        if self._get_delta_time() >= self.log_every:
            self.file_logger.write_results(plots_data, lsds_data, binaries_data)
            self.time = time.time()

    def update(self, proccessed_frame, plots_data, lsds_data, binaries_data):
        if self.show:
            self.gui_handler.update(proccessed_frame, plots_data, lsds_data, binaries_data)
        if self.log_path is not None:
            self.log_in_file(plots_data, lsds_data, binaries_data)
        if self.telegram_api is not None:
            self.telegram_api.update()
class Monitor:
    def __init__(self, camera_id: int=0):
        self.vid = cv2.VideoCapture(camera_id)
        self.vid.set(4, 720)
        self.vid.set(cv2.CAP_PROP_AUTOFOCUS, 0)
        ### КОСТЫЛЬ. КАМЕРА ФОКУСИРУЕТСЯ ИЛИ ЧТО-ТО ТИПА ТОГО
        _, frame = self.vid.read()
        _, frame = self.vid.read()
        _, frame = self.vid.read()
        _, frame = self.vid.read()
        _, frame = self.vid.read()
        _, frame = self.vid.read()
        _, frame = self.vid.read()
        _, frame = self.vid.read()
        _, frame = self.vid.read()
        self.init_time = time.time()

    def _capture_frame(self) -> np.ndarray:
        _, frame = self.vid.read()
        frame = frame / 255
        return frame

    def _update_coordinates(self, controlled_objects: control_objects.ControlObject, frame: np.ndarray):
        controlled_objects.update_similarity(frame)
        old_similarity = controlled_objects.current_similarity
        controlled_objects.update_coordinates(frame)
        new_similarity = controlled_objects.current_similarity

        while not np.allclose(old_similarity, new_similarity):
            old_similarity = new_similarity
            controlled_objects.update_coordinates(frame)
            new_similarity = controlled_objects.current_similarity

    def _add_numbers(self, frame: np.ndarray, coordinates: typing.Iterable[tuple[int, int, int, int]],
                    color: tuple[float, float, float] = (1.0, 0, 0), scale: float = 0.7,
                    thickness: int = 1) -> np.ndarray:
        shift_y = 20  # Hyperparameter
        shift_x = 3  # Hyperparameter
        font = cv2.FONT_HERSHEY_COMPLEX  # Hyperparameter
        for i, coordinate in enumerate(coordinates):
            cv2.putText(
                frame, f"{i + 1}", (coordinate[0] + shift_x, coordinate[1] + shift_y), font, scale, color, thickness
            )
        return frame

    def _highlight_boundaries(self, frame: np.ndarray, coordinates: typing.Iterable[tuple[int, int, int, int]],
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

    def _mark_objects_view(self, frame: np.ndarray, coordinates: typing.Iterable[tuple[int, int, int, int]],
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
                      controlled_objects: typing.Iterable[control_objects.ControlObject]) -> np.ndarray:
        """
        Process the figure adding boundaries for objects, numbers and highlite objects on a picture
        :param frame: The picture in float (0, 1) with shape (height,width, channels) in rgb format
        :param controlled_objects: The objects that controlled under program
        :return:
        """
        coordinates = [controlled_object.current_coordinates for controlled_object in controlled_objects]

        processed_frame = self._mark_objects_view(frame, coordinates)
        processed_frame = self._highlight_boundaries(processed_frame, coordinates, width=3, color=(1.0, 0, 0))
        processed_frame = self._add_numbers(processed_frame, coordinates)
        return processed_frame

    def process_similarities(self, frame: np.ndarray,
                             controlled_objects: typing.Iterable[control_objects.ControlObject],
                             update_pos: bool) -> None:
        """
        Process the figure adding boundaries for objects, numbers and highlight objects on a picture
        :param frame: The picture in float (0, 1) with shape (height,width, channels)
        :param controlled_objects: The objects that controlled under program
        :param update_pos: update positions of the objects
        :return:
        """
        for controlled_object in controlled_objects:
            if update_pos:
                self._update_coordinates(controlled_object, frame)
            controlled_object.update_similarity(frame)
            similarity = controlled_object.current_similarity
            if similarity < controlled_object.min_similarity:
                print(1)
                raise RuntimeError(f"similarity for object {controlled_object.name} is too low {similarity}")

    def collect_object_values(self, frame: np.ndarray,
                               controlled_objects: typing.Iterable[control_objects.ControlObject]):
        values = {}
        for controlled_object in controlled_objects:
            values[controlled_object.name] = controlled_object.get_value(frame)
        return values

    def _get_names(self,controlled_objects: typing.Iterable[control_objects.ControlObject]
                   ) -> tuple[list[str], list[str], list[str]]:
        plots_names = [
            controlled_object.name for controlled_object in controlled_objects
            if controlled_object.type==control_objects.ObjectsType.Plot]

        lcds_names = [
            controlled_object.name for controlled_object in controlled_objects
            if controlled_object.type==control_objects.ObjectsType.Display]

        binaries_names = [
            controlled_object.name for controlled_object in controlled_objects
            if controlled_object.type==control_objects.ObjectsType.Binary]

        return plots_names, lcds_names, binaries_names

    def _get_values(self, frame: np.ndarray,
                    controlled_objects: typing.Iterable[control_objects.ControlObject]
                    ) -> tuple[dict[str, tuple[float, float]], dict[str, float], dict[str, bool]]:
        plots_data = {}
        lsds_data = {}
        binaries_data = {}
        for controlled_object in controlled_objects:
            name = controlled_object.name
            type = controlled_object.type
            value = controlled_object.get_value(frame)
            if type is control_objects.ObjectsType.Plot:
                hour = (time.time() - self.init_time) / 3600
                plots_data[name] = (hour, value)
            elif type is control_objects.ObjectsType.Display:
                lsds_data[name] = value
            elif type is control_objects.ObjectsType.Binary:
                binaries_data[name] = value

        return plots_data, lsds_data, binaries_data

    def _procces_data(self, controlled_objects: typing.Iterable[control_objects.ControlObject], update_pos: bool
                      ) -> tuple[np.ndarray, dict[str, tuple[float, float]], dict[str, float], dict[str, bool]]:
        frame = self._capture_frame()
        self.process_similarities(frame, controlled_objects, update_pos)
        plots_data, lsds_data, binaries_data = self._get_values(frame, controlled_objects)
        return frame, plots_data, lsds_data, binaries_data

    def run_loop(self, controlled_objects: typing.Iterable[control_objects.ControlObject],
                 log_path: None | str | Path=None, show: bool=True, telegram_api: TelegramApi | None=None,
                 update_pos: bool=True, log_every:int=10) -> None:
        """
        :param controlled_objects: The objects that we try to control
        :param show: Show figures with data
        :param telegram_api: telegram_api
        :param update_pos: update positions of the objects
        :param log_every: log every steps
        :return:
        """
        plots_names, lcds_names, binaries_names = self._get_names(controlled_objects)
        with UpdateManager(plots_names, lcds_names, binaries_names,
                           log_path=log_path, show=show, telegram_api=telegram_api,
                           update_pos=update_pos, log_every=log_every) as manager:
            while True:
                frame, plots_data, lsds_data, binaries_data = self._procces_data(controlled_objects, update_pos)
                proccessed_frame = self.process_view(frame=frame, controlled_objects=controlled_objects)
                manager.update(proccessed_frame, plots_data, lsds_data, binaries_data)

    def release_camera(self):
        self.vid.release()