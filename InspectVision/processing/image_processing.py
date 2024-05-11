import cv2
import numpy as np

ExpTime = 1e-7

class ImageProcessor:
    _camera_ids = set()
    def __new__(cls, camera_id: int=1, exp_time: float=ExpTime):
        if camera_id in cls._camera_ids:
            raise ValueError("You have already created the ImageProcessor with current id. Please, use it")
        cls._camera_ids.add(camera_id)
        return super().__new__(cls)

    def __init__(self, camera_id:int=1, exp_time:float=ExpTime):
        self.__vid = cv2.VideoCapture(camera_id)
        self.exp_time = exp_time
        self._set_properties()

    @property
    def vid(self) -> cv2.VideoCapture:
        return self.__vid

    def _set_properties(self) -> None:
        pass
        #self.__vid.set(3, 1280)
        #self.__vid.set(4, 720)
        self.__vid.set(cv2.CAP_PROP_AUTOFOCUS, 1)
        self.__vid.set(cv2.CAP_PROP_EXPOSURE, self.exp_time)

    def release(self) -> None:
        self.__vid.release()

    def check_open(self) -> bool:
        return self.__vid.isOpened()

    def capture_frame(self) -> np.ndarray:
        """
        :return: frame in RGB color format with shape (width, height, channels) in values in range (0, 1)
        """
        _, frame = self.vid.read()
        _, frame = self.vid.read()
        _, frame = self.vid.read()
        _, frame = self.vid.read()
        _, frame = self.vid.read()
        _, frame = self.vid.read()
        _, frame = self.vid.read()
        _, frame = self.vid.read()
        _, frame = self.vid.read()

        frame = frame / 255
        return frame

def select_roi(image_processor: ImageProcessor):
    """
    Give the interface to point roi on a frame
    :param image_processor: ImageProcessor instant
    :return:
    """
    frame = image_processor.capture_frame()
    rois = cv2.selectROIs("Select Rois", frame)
    return frame, rois

def main():
    image_processor = ImageProcessor()
    print(image_processor)


if __name__=="__main__":
    main()