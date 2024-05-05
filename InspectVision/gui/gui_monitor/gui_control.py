import sys
import typing as tp
import warnings

import numpy as np

from PyQt6.QtWidgets import (QApplication, QMainWindow)
from PyQt6 import QtCore
from PyQt6.QtGui import QImage, QPixmap

from .gui_interface import Ui_WindowBuilder


class WindowUpdater(QtCore.QObject):
    data_recieved = QtCore.pyqtSignal(object, object, object)
    screen_recieved = QtCore.pyqtSignal(np.ndarray)
    def emit_data(self, plots_data=None, lcds_data=None, binaries_data=None):
        self.data_recieved.emit(plots_data, lcds_data, binaries_data)

    def emit_screen(self, frame: np.ndarray):
        self.screen_recieved.emit(frame)


class MainWindow(QMainWindow):
    def __init__(self, plots_name, lcds_name, binaries_name):
        super(MainWindow, self).__init__()
        window_factory = Ui_WindowBuilder(main_window_size=(1500, 900),
                                          plots_name=plots_name, lcds_name=lcds_name, binaries_name=binaries_name)
        self.ui = window_factory.get_ui_window(self)

    def _update_data_plots(self, plots_data: dict[str, tuple[float, float]]):
        for plot_name, values in plots_data.items():
            self.ui.plots[plot_name].plot([values[0]], [values[1]], symbol="o")

    def _update_data_binaries_status(self, updated_status: dict[str, bool]):
        for binaries_name, value in updated_status.items():
            self.ui.binaries[binaries_name].display(value)

    def _update_data_lcds(self, updated_lcds_values: dict[str, float]):
        for lcd_name, value in updated_lcds_values.items():
            self.ui.lcds[lcd_name].display(value)

    def update_values(self,
               plots_data: dict[str, tuple[float, float]] | None,
               updated_lcds_values: dict[str, float] | None,
               updated_status: dict[str, bool] | None):
        if plots_data is not None:
            self._update_data_plots(plots_data)
        if updated_status is not None:
            self._update_data_binaries_status(updated_status)
        if updated_lcds_values is not None:
            self._update_data_lcds(updated_lcds_values)

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
    def __init__(self, plots_name: list[str], lcds_name: list[str], binaries_name: list[str]):
        self.app = QApplication([])

        self.plot_name = plots_name
        self.lcds_name = lcds_name
        self.binaries_name = binaries_name

        self.window = MainWindow(plots_name, lcds_name, binaries_name)
        self.window.show()

        self.updater = WindowUpdater()
        self.updater.data_recieved.connect(self.window.update_values)
        self.updater.screen_recieved.connect(self.window.update_screen)

    def __enter__(self):
        return self

    def _get_missing_keys(self, names: list[str], updating_data: dict[str, tp.Any]):
        missing_keys = [key for key in updating_data.keys() if key not in names]
        return missing_keys

    def _get_updating_data(self, init_names: list[str], updating_data: dict[str, tp.Any]):
        if not (set(updating_data.keys()) <= set(init_names)):
            missing_keys = self._get_missing_keys(init_names, updating_data)
            warnings.warn(
                "some keys don't exist in initial names {}, I am using only existing keys".format(missing_keys))
            new_updating_data = {key: value for key, value in updating_data.items() if key not in missing_keys}
            return new_updating_data
        else:
            return updating_data

    def update(self, screen: np.ndarray | None,
               plots_data: dict[str, tuple[float, float]] | None = None,
               lcds_data: dict[str, float] | None = None,
               binaries_data: dict[str, bool] | None = None) -> None:
        if plots_data is not None:
            plots_data = self._get_updating_data(self.plot_name, plots_data)
        if lcds_data is not None:
            lcds_data = self._get_updating_data(self.lcds_name, lcds_data)
        if binaries_data is not None:
            binaries_data = self._get_updating_data(self.binaries_name, binaries_data)

        self.updater.emit_data(plots_data=plots_data, lcds_data=lcds_data, binaries_data=binaries_data)
        if screen is not None:
            self.updater.emit_screen(screen)
        QApplication.processEvents()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.exit()

    def exit(self):
        sys.exit(self.app.exec())
