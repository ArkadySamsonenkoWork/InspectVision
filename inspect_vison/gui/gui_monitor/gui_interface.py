from enum import Enum
from dataclasses import dataclass
from datetime import datetime
import typing as tp

import pyqtgraph as pg
from PyQt6.QtCore import QCoreApplication, QMetaObject, QRect
from PyQt6.QtWidgets import QGraphicsView, QLineEdit, QMainWindow, QLCDNumber, QWidget, QLabel


class MC(type(Enum)):
  def __repr__(self):
      text = """
      Class with types of widget.
      Available Widgets Representations.
      ..............................................
      Plot is a simple plot with dependence on time.
      Display is a LCD Display with seven-segment digits.
      Binary is a status widget with only two value: On, OFF.
      ..............................................
      """
      return text

class WidgetType(Enum, metaclass=MC):
    Plot = 0
    Display = 1
    Binary = 2


def split_box(box: QRect, attitude: float = 0.6) -> tuple[QRect, QRect]:
    """
    :param box: the box that must be splited
    :param attitude: the attitude of the first final box to the init box.
    :return: Two boxes after splitting. Their total width and height are equal to the init box sizes
    """
    x_box, y_box, width, height = box.x(), box.y(), box.width(), box.height()
    width_box_1 = int(attitude * width)
    width_box_2 = width - width_box_1
    box_1 = QRect(x_box, y_box, width_box_1, height)
    box_2 = QRect(x_box + width_box_1, y_box, width_box_2, height)
    return box_1, box_2


class WidgetInterface(QWidget):
    def display(self, data: tp.Any):
        pass


class BinaryStatusWidget(QWidget):
    def __init__(self, centralwidget: QWidget) -> None:
        super().__init__(centralwidget)
        self.lineEdit_name = QLineEdit(self)
        self.lineEdit_status = QLineEdit(self)

    def setGeometry(self, box: QRect) -> None:
        name_box, status_box = split_box(box)
        self.lineEdit_name.setGeometry(name_box)
        self.lineEdit_status.setGeometry(status_box)

    def set_name(self, name: str):
        self.lineEdit_name.setText(QCoreApplication.translate("MainWindow", name, None))

    def display(self, data: bool):
        if data:
            self.lineEdit_status.setStyleSheet(u"background-color: rgb(0, 100, 0);\n"
                                                "color: rgb(255, 255, 255);\n")
            self.lineEdit_status.setText(QCoreApplication.translate("MainWindow", "ON", None))

        else:
            self.lineEdit_status.setStyleSheet(u"background-color: rgb(150, 50, 50);\n"
                                                "color: rgb(0, 0, 0);\n")
            self.lineEdit_status.setText(QCoreApplication.translate("MainWindow", "OFF", None))

    def setReadOnly(self, read_only: bool):
        self.lineEdit_name.setReadOnly(read_only)
        self.lineEdit_status.setReadOnly(read_only)


class PlotWidget(pg.PlotWidget):
    def __init__(self, central_widget: QWidget, title: str, time_delta: float=6):
        super().__init__(central_widget, title=title)
        self.time_delta = time_delta * 60 * 60  # To seconds
        self.setLabel("bottom", "Time (minutes)")
        self.addLegend()
        self.showGrid(x=True, y=True)
        self.previous_data = datetime.now()
        self.data = {"x": [], "y": []}

        axis = pg.DateAxisItem()
        self.setAxisItems({'bottom': axis})

    def display(self, data: tuple[datetime, float]):
        if (data[0] - self.previous_data).total_seconds() >= self.time_delta:
            self.data["x"].pop(0), self.data["y"].pop(0)
        self.data["x"].append(data[0].timestamp()), self.data["y"].append(data[1])
        self.plot(self.data["x"], self.data["y"], clear=True)


class TitledLCDWidget(QWidget):
    def __init__(self, centralwidget: QWidget) -> None:
        super().__init__(centralwidget)
        self.lineEdit_name = QLineEdit(self)
        self.lcdNumber = QLCDNumber(self)
        self.lineEdit_name.setStyleSheet(u"background-color: rgb(100, 100, 100);\n"
                                          "color: rgb(255, 255, 255);")
        self.lcdNumber.setStyleSheet(u"color: rgb(255, 255, 255);\n"
                                            "background-color: rgb(100, 100, 100);")

    def setGeometry(self, box: QRect) -> None:
        name_box, lcd_box = split_box(box)
        self.lineEdit_name.setGeometry(name_box)
        self.lcdNumber.setGeometry(lcd_box)

    def set_name(self, name: str) -> None:
        self.lineEdit_name.setText(QCoreApplication.translate("MainWindow", name, None))

    def display(self, data: str | float) -> None:
        self.lcdNumber.display(data)

    def setReadOnly(self, read_only: bool) -> None:
        self.lineEdit_name.setReadOnly(read_only)



class WidgetsBuilder:
    @staticmethod
    def get_plot(centralwidget: QWidget, box: QRect, title: str) -> PlotWidget:
        plot = PlotWidget(centralwidget, title=title)
        plot.setObjectName(title)
        plot.setGeometry(box)
        return plot

    @staticmethod
    def get_titled_lcd(centralwidget: QWidget, box: QRect, title: str) -> TitledLCDWidget:
        titled_lcd = TitledLCDWidget(centralwidget)
        titled_lcd.setObjectName(u"titled_lcd")
        titled_lcd.setGeometry(box)
        titled_lcd.setReadOnly(True)
        titled_lcd.set_name(title)
        return titled_lcd

    @staticmethod
    def get_binary_status(centralwidget: QWidget, box: QRect, title: str, status: bool) -> BinaryStatusWidget:
        binary_widget = BinaryStatusWidget(centralwidget)
        binary_widget.setObjectName(u"status_widget")
        binary_widget.setGeometry(box)
        binary_widget.setReadOnly(True)
        binary_widget.set_name(title)
        binary_widget.display(status)
        return binary_widget

    @staticmethod
    def get_screen_veiw(centralwidget: QWidget, box: QRect) -> QLabel:
        screenView = QLabel(centralwidget)
        screenView.setObjectName(u"screenView")
        screenView.setGeometry(box)
        return screenView


@dataclass
class SizeParameters:
    half_monitor_factor: float = 9 / 20
    widgets_delta_width: int = 20
    widgets_delta_height: int = 20
    binary_width: int = 50
    binary_height: int = 30
    double_widgets_line_quantity: int = 4


class WindowParameters:
    def __init__(self):
        self.parameters = SizeParameters()

    def screen_view_size(self, main_window_size: tuple[int, int]) -> tuple[int, int]:
        width = int(main_window_size[0] * self.parameters.half_monitor_factor)
        height = int(main_window_size[1] * self.parameters.half_monitor_factor)
        return width, height

    def plot_size(self, main_window_size: tuple[int, int]) -> tuple[int, int]:
        width = int(main_window_size[0] * self.parameters.half_monitor_factor)
        height = (main_window_size[1] - int(main_window_size[1] * self.parameters.half_monitor_factor)) // 3
        return width, height

    def double_widgets_size(self, main_window_size: tuple[int, int]) -> tuple[int, int]:
        width = int(main_window_size[0] * self.parameters.half_monitor_factor) // 5
        height = main_window_size[1] // 20
        return width, height


class Ui_WindowBuilder:
    def __init__(self, main_window_size: tuple[int, int], name_type: dict[str, WidgetType]):
        self.main_window_size = main_window_size
        self.window_parameters = WindowParameters()
        self._get_widgets_names(name_type)

    def _get_widgets_names(self, name_type: dict[str, WidgetType]):
        self.plots_name = []
        self.lcds_name = []
        self.binaries_name = []
        for name, gui_type in name_type.items():
            if gui_type == WidgetType.Plot:
                self.plots_name.append(name)
            elif gui_type == WidgetType.Display:
                self.lcds_name.append(name)
            elif gui_type == WidgetType.Binary:
                self.binaries_name.append(name)
        self.plots_quantity = len(self.plots_name)
        self.lcds_quantity = len(self.lcds_name)
        self.binaries_quantity = len(self.binaries_name)

    def _get_screen_box(self) -> QRect:
        window_parameters = self.window_parameters
        width, height = window_parameters.screen_view_size(self.main_window_size)
        screen_view_box = QRect(window_parameters.parameters.widgets_delta_width,
                                window_parameters.parameters.widgets_delta_height,
                                width, height)
        return screen_view_box

    def _get_plot_box(self, plot_counter: int) -> QRect:
        window_parameters = self.window_parameters
        width_screen, height_screen = window_parameters.screen_view_size(self.main_window_size)
        width_plot, height_plot = window_parameters.plot_size(self.main_window_size)
        top_position =\
            height_screen +\
            plot_counter * height_plot +\
            (2 + plot_counter) * window_parameters.parameters.widgets_delta_height
        plot_view_box = QRect(window_parameters.parameters.widgets_delta_width,
                              top_position,
                              width_plot, height_plot)
        return plot_view_box

    def _get_double_widget_box(self, line: int, column: int) -> QRect:
        window_parameters = self.window_parameters
        width, height = window_parameters.double_widgets_size(self.main_window_size)
        left = int(self.main_window_size[0] * (1 - window_parameters.parameters.half_monitor_factor)) +\
               (column + 1) * window_parameters.parameters.widgets_delta_width + column * width
        top = (line + 1) * window_parameters.parameters.widgets_delta_width + line * height

        double_widget_box = QRect(left, top, width, height)
        return double_widget_box

    def _get_binary_box(self, binary_counter: int) -> QRect:
        window_parameters = self.window_parameters
        line = binary_counter // window_parameters.parameters.double_widgets_line_quantity
        column = binary_counter %  window_parameters.parameters.double_widgets_line_quantity

        return self._get_double_widget_box(line, column)

    def _get_lcd_box(self, lcd_counter: int) -> QRect:
        window_parameters = self.window_parameters
        delta_line = self.binaries_quantity // window_parameters.parameters.double_widgets_line_quantity + 1
        line = lcd_counter // window_parameters.parameters.double_widgets_line_quantity + delta_line
        column = lcd_counter %  window_parameters.parameters.double_widgets_line_quantity

        return self._get_double_widget_box(line, column)


    def _get_widgets(self, widgets_factory: WidgetsBuilder, centralwidget: QWidget) -> dict[str, WidgetInterface]:
        plots =\
            {name: widgets_factory.get_plot(centralwidget, self._get_plot_box(i), title=name)
            for i, name in enumerate(self.plots_name)}
        lcds =\
            {name: widgets_factory.get_titled_lcd(
                centralwidget, self._get_lcd_box(i), title=name,
            ) for i, name in enumerate(self.lcds_name)}
        binaries_status =\
            {name: widgets_factory.get_binary_status(
                centralwidget, self._get_binary_box(i), title=name, status=True
            ) for i, name in enumerate(self.binaries_name)}

        widgets = {}
        widgets.update(plots)
        widgets.update(lcds)
        widgets.update(binaries_status)

        return widgets

    def get_ui_window(self, MainWindow: QMainWindow):
        ui_mainwindow = Ui_MainWindow()
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(self.main_window_size[0], self.main_window_size[1])

        centralwidget = QWidget(MainWindow)
        centralwidget.setObjectName(u"centralwidget")

        widgets_factory = WidgetsBuilder()
        screen_view_box = self._get_screen_box()

        screenView = widgets_factory.get_screen_veiw(centralwidget, screen_view_box)

        widgets = self._get_widgets(widgets_factory, centralwidget)
        ui_mainwindow.setupUi(screenView, widgets)

        MainWindow.setCentralWidget(centralwidget)
        MainWindow.setWindowTitle(
            QCoreApplication.translate("MainWindow", u"MainWindow", None)
        )
        QMetaObject.connectSlotsByName(MainWindow)
        return ui_mainwindow

class Ui_MainWindow():
    def setupUi(self, screen_view: QLabel,
                widgets: dict[str, WidgetInterface]) -> None:
        self.screenView = screen_view
        self.widgets = widgets


