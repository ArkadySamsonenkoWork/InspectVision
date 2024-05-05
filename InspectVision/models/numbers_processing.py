import typing as tp

import numpy as np
import matplotlib.pyplot as plt
import cv2
import onnxruntime

import imutils
from imutils import contours

def get_thresh_image(image: np.ndarray, marker_regime="auto") -> np.ndarray:
    """
    Make image intensive and
    :param image: image in the format: height, width, channel, in uint8 from 0 to 255
    :param marker_regime: reverse, direct, auto
    :return:
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (1, 5))
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)

    direct_flag = True
    if marker_regime == "auto":
        mean_color = thresh.mean()
        direct_flag = (mean_color < 255 // 2)
    elif marker_regime == "direct":
        direct_flag = True
    elif marker_regime == "reverse":
        direct_flag = False
    else:
        raise ValueError("marker_regime must be auto / direct / reverse")

    if direct_flag:
        return thresh
    else:
        return 255 - thresh


def erode_image(thresh: np.ndarray, size: int=10) -> np.ndarray:
    """
    erode image
    :param thresh: thresh image in the format: height, width in uint8 from 0 to 255
    :param size: kernel size for erosion
    :return: eroded image
    """
    kernel = np.ones((size, size // 4), np.uint8)
    dilation = cv2.dilate(thresh, kernel, iterations = 2)
    erosion = cv2.erode(dilation, kernel, iterations = 2)
    return erosion


def find_contours(erosion: np.ndarray) -> list[np.ndarray]:
    """
    :param erosion: eroded image in the format: height, width in uint8 from 0 to 255
    :param image: init image in the format: channels height, width in uint8 from 0 to 255
    :return: tuple of image with box and contours with digits
    """
    cnts = cv2.findContours(erosion.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts = imutils.grab_contours(cnts)
    digitCnts = []
    #image_w_bbox = image.copy()
    h_image, w_image = erosion.shape
    for c in cnts:
        (x, y, w, h) = cv2.boundingRect(c)
        if w >= w_image // 100 and (h_image // 2 <= h <= h_image):
            digitCnts.append(c)
            #image_w_bbox = cv2.rectangle(image_w_bbox, (x, y), (x + w, y + h), (0, 255, 0), 2.jpg)
    digitCnts = contours.sort_contours(digitCnts, method="left-to-right")[0]
    #return image_w_bbox, digitCnts
    return digitCnts


def pad_image(roi: np.ndarray):
    """
    :param roi:
    :return:
    """
    h, w = roi.shape
    if w < h:
        left_size = (h - w) // 2
        right_size = h - (w + left_size)
        roi = np.pad(roi, ((0, 0), (left_size, right_size)))
    else:
        top_size = (w - h) // 2
        low_size = w - (h + top_size)
        roi = np.pad(roi, ((top_size, low_size), (0, 0)))
    return roi


class DigitClassifierModel:
    """
    model for classification numbers
    """
    def __init__(self, path, shape: tuple):
        """
        :param path: path to onnx model to recognize digits
        :param shape: shape of input image
        """
        self.session = onnxruntime.InferenceSession(path, None)
        self.shape = shape

    def __call__(self, roi: np.ndarray) -> int:
        """
        :param roi: roi of the digit. It must be 0, 255 image in shape (height, width).
        height should be equal to width and interpolated to 28 size
        :return: digit
        """
        roi = roi.astype(np.float32)
        roi[roi < 255 / 2] = 0.0
        roi[roi >= 255 / 2] = 1.0
        roi = np.resize(roi, new_shape=self.shape)
        plt.imshow(roi[0, 0])
        plt.show()
        input_name = self.session.get_inputs()[0].name
        output_name = self.session.get_outputs()[0].name
        result = self.session.run([output_name], {input_name: roi})
        prediction = int(np.argmax(np.array(result).squeeze(), axis=0))
        print(prediction)
        return prediction


def get_digits(digitCnts: list[np.ndarray], erosion: np.ndarray, classifier: tp.Callable) -> list[int]:
    """
    :param digitCnts: contour with digit
    :param erosion: eroded image with black digit on white background
    :param classifier: model that classifies digits
    :return: classified digits
    """
    digits = []
    for c in digitCnts:
        (x, y, w, h) = cv2.boundingRect(c)
        roi = erosion[y:y + h, x:x + w]
        roi = pad_image(roi)
        roi = cv2.resize(roi, dsize=(28, 28), interpolation=cv2.INTER_AREA)
        number = classifier(roi)
        digits.append(number)
    return digits

def main():
    image = cv2.imread("test_pictures/digit_numbers_led_3")
    height = 100
    image = imutils.resize(image, height=height)
    thresh = get_thresh_image(image)
    erosion = erode_image(thresh, height // 50)
    box, contiurs = find_contours(erosion)

    path = "onnx_models/DigitClassifier.onnx"
    shape = (1, 1, 28, 28)
    model = DigitClassifierModel(path, shape)
    _ = get_digits(contiurs, erosion, model)
    #cv2.imshow("edge", box)
    #cv2.waitKey(10000)
    #print(image.shape)

