# import the opencv library
import cv2
import numpy as np
import gui
import control_objects
import objects_handler
from processing import image_processing
from data_logging import Notificator, TelegramApi

class ChillerNotificator(Notificator):
    def check_conditions(self):
        condition = self.controlled_objects["hight_temperature_detector"] > 17.8
        message = "The water temerature is hight!!!!!"
        return condition, message


#image_processor = utils.ImageProcessor() # create ImageProsessor
#objects_coord = image_processor.select_objects() # select objects
# or manual
def main():
    image_processor = image_processing.ImageProcessor(0)
    frame, rois = image_processor.select_objects()
    # or manual
    controlled_objects = []

    """
    controlled_objects.append(
        control_objects.LedDigits(name="hight_temperature_detector", coordinates=rois[0],
                                  init_value=17.8, frame=frame, type=control_objects.ObjectsType.Plot)
    )
    controlled_objects.append(
        control_objects.LedDigits(name="low_temperature_detector", coordinates=rois[1],
                                  init_value=16.8, frame=frame, type=control_objects.ObjectsType.Plot)
    )

    """
    controlled_objects.append(
        control_objects.Bulb(name="bulb_1", coordinates=rois[0],
                                  init_value=1, frame=frame, type=control_objects.ObjectsType.Binary)
    )

    controlled_objects.append(
        control_objects.Bulb(name="bulb_21", coordinates=rois[1],
                                  init_value=0, frame=frame, type=control_objects.ObjectsType.Binary)
    )
    # ...........................
    monitor = objects_handler.Monitor(camera_id=0)
    path = "data"
    monitor.run_loop(controlled_objects, show=True, telegram_api=None, log_path=path, log_every=2)


main()
