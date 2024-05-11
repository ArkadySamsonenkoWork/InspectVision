import cv2
from InspectVision import gui, handlers, managing
from InspectVision.processing import image_processing
from InspectVision.data_logging import Notificator, TelegramApi

class ChillerNotificator(Notificator):
    def check_conditions(self):
        condition = self.update_values["hight_temperature_detector"] > 17.8
        message = "The water temerature is hight!!!!!"
        return [condition], [message]


#image_processor = utils.ImageProcessor() # create ImageProsessor
#objects_coord = image_processor.select_objects() # select objects
# or manual
def main():
    image_processor = image_processing.ImageProcessor(2)
    frame, rois = image_processing.select_roi(image_processor)
    # or manual
    controlled_objects = []

    """
    controlled_objects.append(
        control_objects.LedDigits(name="hight_temperature_detector", coordinates=rois[0],
                                  init_value=17.8, frame=frame, type=control_objects.ObjectsType.Plot)
    )
    """
    controlled_objects.append(
        handlers.LedDigits(name="low_temperature_detector", coordinates=rois[1],
                                  init_value=18.2, frame=frame, gui_type=gui.WidgetType.Plot)
    )

    controlled_objects.append(
        handlers.Bulb(name="bulb_1", coordinates=rois[0],
                                  init_value=1, frame=frame, gui_type=gui.WidgetType.Binary)
    )

    controlled_objects.append(
        handlers.Bulb(name="bulb_2", coordinates=rois[1],
                                  init_value=0, frame=frame, gui_type=gui.WidgetType.Binary)
    )
    # ...........................
    monitor = managing.Monitor(image_processor)
    path = "data"
    monitor.run_loop(controlled_objects, show=True, telegram_api=None, log_path=path, log_every=2)



main()