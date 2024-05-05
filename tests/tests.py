import matplotlib.pyplot as plt
import cv2
import pytest

import InspectVision.control_objects as control_objects
import InspectVision.gui as gui
import InspectVision.models as models
from InspectVision.processing import objects_handler

base_frame_path = "tests/test_pictures/base_frame.jpg"
object_parameters = pytest.mark.parametrize(
    [
        "coordinates",
        "check_frame_path",
    ],
    [
        (
            (310, 360, 120, 80),
            "tests/test_pictures/2.jpg",
        ),
        (
            (310, 360, 120, 80),
            "tests/test_pictures/3.jpg",
        ),
        (
            (310, 360, 120, 80),
            "tests/test_pictures/4.jpg",
        ),
        (
            (355, 440, 80, 80),
            "tests/test_pictures/2.jpg",
        ),
        (
            (355, 440, 80, 80),
            "tests/test_pictures/3.jpg",
        ),
        (
            (355, 440, 80, 80),
            "tests/test_pictures/4.jpg",
        ),
    ],
)

@object_parameters
def test_update_coordinates(coordinates, check_frame_path):
    base_frame = cv2.imread(base_frame_path)
    check_frame = cv2.imread(check_frame_path)
    x1 = coordinates[0]
    y1 = coordinates[1]
    x2 = coordinates[2]
    y2 = coordinates[3]
    control_object = control_objects.Bulb(coordinates, base_frame, type=control_objects.ObjectsType.Binary)

    control_object.update_similarity(check_frame)
    old_similarity = control_object.current_similarity
    for _ in range(20):
        control_object.update_coordinates(check_frame)
        new_similarity = control_object.current_similarity
        assert new_similarity >= old_similarity, "New similarity must be greater than old one"
        old_similarity = new_similarity

    control_object.update_similarity(base_frame)
    old_similarity = control_object.current_similarity
    for _ in range(20):
        control_object.update_coordinates(base_frame)
        new_similarity = control_object.current_similarity
        assert new_similarity >= old_similarity, "New similarity must be greater than old one"
        old_similarity = new_similarity
    assert pytest.approx(old_similarity) == 1

@pytest.fixture(scope="function")
def manual_capturing():
    vid = cv2.VideoCapture(0)
    _, frame = vid.read()
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    vid.release()
    frame = frame / 255
    coordinates = [(300, 230, 40, 40), (400, 230, 40, 40)]
    obj_1 = control_objects.Bulb(coordinates[0], frame, init_value=0.4, name="1", type=control_objects.ObjectsType.Binary)
    obj_2 = control_objects.Bulb(coordinates[1], frame, init_value=0.4, name="1", type=control_objects.ObjectsType.Binary)

    monitor = objects_handler.Monitor()
    monitor.run_loop((obj_1, obj_2))
    return True

def test_manual_capturing(manual_capturing):
    assert manual_capturing

def test_bulb():
    image_on = cv2.imread("tests/test_pictures/bulb_on.jpg")
    image_off = cv2.imread("tests/test_pictures/bulb_off.jpg")
    print(image_on)
    max_margin = 0.2
    model_on = models.BulbModel(1, image_on, max_margin)
    model_off = models.BulbModel(0, image_off, max_margin)

    anwer_on = model_on(image_on)
    anwer_off = model_on(image_off)
    assert anwer_on
    assert not anwer_off

    anwer_on = model_off(image_on)
    anwer_off = model_off(image_off)
    assert anwer_on
    assert not anwer_off

def test_led_digits():
    led_1 = cv2.imread("tests/test_pictures/digit_numbers_led_3.jpg")
    led_2 = cv2.imread("tests/test_pictures/digit_numbers_led_4.jpg")
    init_value_1 = 15.2
    init_value_2 = 17.9
    model_led_1 = models.LedNumbersModel(15.2, led_1)
    model_led_2 = models.LedNumbersModel(17.9, led_2)

    answer_1 = model_led_1(led_2)
    answer_2 = model_led_2(led_1)

    assert answer_1 == str(init_value_2)
    assert answer_2 == str(init_value_1)