import cv2
from InspectVision import gui, control_objects, objects_handler
from InspectVision.processing import image_processing
from InspectVision.data_logging import Notificator, TelegramApi

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
    frame, rois = image_processing.select_roi(image_processor)
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
                                  init_value=1, frame=frame, gui_type=gui.WidgetType.Binary)
    )

    controlled_objects.append(
        control_objects.Bulb(name="bulb_2", coordinates=rois[1],
                                  init_value=0, frame=frame, gui_type=gui.WidgetType.Binary)
    )
    # ...........................
    monitor = objects_handler.Monitor(image_processor)
    path = "data"
    monitor.run_loop(controlled_objects, show=True, telegram_api=None, log_path=path, log_every=2)



def automatic_brightness_and_contrast(image, clip_hist_percent=1):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Calculate grayscale histogram
    hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
    hist_size = len(hist)

    # Calculate cumulative distribution from the histogram
    accumulator = []
    accumulator.append(float(hist[0]))
    for index in range(1, hist_size):
        accumulator.append(accumulator[index - 1] + float(hist[index]))

    # Locate points to clip
    maximum = accumulator[-1]
    clip_hist_percent *= (maximum / 100.0)
    clip_hist_percent /= 2.0

    # Locate left cut
    minimum_gray = 0
    while accumulator[minimum_gray] < clip_hist_percent:
        minimum_gray += 1

    # Locate right cut
    maximum_gray = hist_size - 1
    while accumulator[maximum_gray] >= (maximum - clip_hist_percent):
        maximum_gray -= 1

    # Calculate alpha and beta values
    alpha = 255 / (maximum_gray - minimum_gray)
    beta = -minimum_gray * alpha

    auto_result = cv2.convertScaleAbs(image, alpha=alpha, beta=beta)
    return auto_result, alpha, beta

main()