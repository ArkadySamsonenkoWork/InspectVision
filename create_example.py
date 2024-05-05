from InspectVision.gui.gui_monitor import GuiHandler
from InspectVision.objects_handler import Monitor

import time
import numpy as np
import cv2
import imutils

class Mon(Monitor):
    def process_view(self, frame: np.ndarray, coordinates) -> np.ndarray:
        """
        Process the figure adding boundaries for objects, numbers and highlite objects on a picture
        :param frame: The picture in float (0, 1) with shape (height,width, channels) in rgb format
        :param controlled_objects: The objects that controlled under program
        :return:
        """
        processed_frame = self._mark_objects_view(frame, coordinates)
        processed_frame = self._highlight_boundaries(processed_frame, coordinates, width=3, color=(1.0, 0, 0))
        processed_frame = self._add_numbers(processed_frame, coordinates)
        return processed_frame


def exampele_1():
    plots_name = ["Канал высокой температуры", "Канал низкой температуры"]
    binaries_name = ["Авария_1", "Авария_2", "Сеть", "Насос_1", "Насос_2"]
    frame = cv2.imread("Screenshots/image.jpeg")
    rois = cv2.selectROIs("Select Rois", frame)
    frame = frame / 255
    monitor = Mon()
    processed_frame = monitor.process_view(frame, rois)
    imutils.resize(processed_frame, width=60)
    gui_handler = GuiHandler(plots_name, lcds_name=[], binaries_name=binaries_name)
    for i in range(100):
        random_number_1 = 17.6 + np.random.random() / 10
        random_number_2 = 17.4 + np.random.random() / 10
        plots_data = {"Канал высокой температуры": (i / 100, random_number_1),
                      "Канал низкой температуры": (i / 100, random_number_2)}
        binaries_data = {"Авария_1": False, "Авария_2": False,
                         "Сеть": False, "Насос_1": True, "Насос_2": True}
        gui_handler.update(processed_frame, plots_data, {}, binaries_data)

def exampele_2():
    binaries_name = ["Pumper_1", "Pumper_2"]
    frame = cv2.imread("Screenshots/image.jpeg")
    rois = cv2.selectROIs("Select Rois", frame)
    frame = frame / 255
    monitor = Mon()
    processed_frame = monitor.process_view(frame, rois)
    processed_frame = imutils.resize(processed_frame, width=600)
    gui_handler = GuiHandler([], lcds_name=[], binaries_name=binaries_name)
    for i in range(10000):
        random_number_1 = 17.6 + np.random.random() / 10
        random_number_2 = 17.4 + np.random.random() / 10
        binaries_data = {"Pumper_1": True, "Pumper_2": True}
        gui_handler.update(processed_frame, {}, {}, binaries_data)


exampele_2()