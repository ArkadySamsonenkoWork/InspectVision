import sys
import typing as tp
import warnings

import numpy as np

from PyQt6.QtWidgets import (QApplication, QMainWindow)
from PyQt6 import QtCore
from PyQt6.QtGui import QImage, QPixmap

from .gui_interface import Ui_WindowBuilder, WidgetType


class WindowUpdater(QtCore.QObject):
    data_recieved = QtCore.pyqtSignal(dict)
    screen_recieved = QtCore.pyqtSignal(np.ndarray)
    def emit_data(self, update_data):
        self.data_recieved.emit(update_data)

    def emit_screen(self, frame: np.ndarray):
        self.screen_recieved.emit(frame)


class MainWindow(QMainWindow):
    def __init__(self, name_type: dict[str, WidgetType]):
        super(MainWindow, self).__init__()
        window_factory = Ui_WindowBuilder(main_window_size=(1500, 900), name_type=name_type)
        self.ui = window_factory.get_ui_window(self)

    def update_values(self, update_data: dict[str, tp.Any]) -> None:
        for name, value in update_data.items():
            self.ui.widgets[name].display(value)

    def update_screen(self, frame: np.ndarray):
        """
        :param frame: in (width, height, channels) format with values from 0 to 1
        :return:
        """
        transformed_frame = (frame * 255).copy()
        #transformed_frame = np.require(transformed_frame, np.uint8, 'C')
        transformed_frame = transformed_frame.astype(np.uint8)
        convert = QImage(transformed_frame, transformed_frame.shape[1], transformed_frame.shape[0], QImage.Format.Format_BGR888)
        pixmap = QPixmap.fromImage(convert)
        self.ui.screenView.setPixmap(pixmap)


class GuiHandler:
    def __init__(self, name_type: dict[str, WidgetType]):
        self.app = QApplication([])
        self.name_type = name_type
        self.window = MainWindow(name_type)
        self.window.show()

        self.updater = WindowUpdater()
        self.updater.data_recieved.connect(self.window.update_values)
        self.updater.screen_recieved.connect(self.window.update_screen)

    def __enter__(self):
        return self

    def _get_existing_keys(self, init_names: tp.Iterable[str], update_names: tp.Iterable[str]):
        existing_keys = [key for key in update_names if key in init_names]
        return existing_keys

    def _get_update_data(self, update_data: dict[str, tp.Any]):
        update_names = update_data.keys()
        init_names = self.name_type.keys()
        if not init_names <= update_names:
            existing_keys = self._get_existing_keys(init_names, update_names)
            warnings.warn(
                "some keys don't exist in initial names {}, I am using only existing keys".format(existing_keys))
            new_updating_data = {key: value for key, value in update_data.items() if key in existing_keys}
            return new_updating_data
        else:
            return update_data

    def update(self, screen: np.ndarray | None, update_data: dict[str, tp.Any] | None = None) -> None:
        if update_data is not None:
            update_data = self._get_update_data(update_data)
            self.updater.emit_data(update_data)
        if screen is not None:
            self.updater.emit_screen(screen)
        QApplication.processEvents()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.exit()

    def exit(self):
        sys.exit(self.app.exec())
