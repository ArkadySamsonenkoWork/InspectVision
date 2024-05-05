import typing
from pathlib import Path
import time

import cv2
import numpy as np
import matplotlib.pyplot as plt
import tkinter as tk

import control_objects

class ImageLabeler:
    def __init__(self, root, image, class_names):
        self.root = root
        self.class_names = class_names
        self.selected_class = None

        self.image = image
        self.display_image()

        self.label_frame = tk.Frame(root)
        self.label_frame.pack()

        self.create_label_buttons()

    def display_image(self):
        img = cv2.cvtColor(self.image, cv2.COLOR_BGR2RGB)
        #img = self.image
        height, width, _ = img.shape
        img = cv2.resize(img, (width // 8, height // 8))  # Adjust size if necessary
        img = tk.PhotoImage(data=cv2.imencode('.png', img)[1].tobytes())
        panel = tk.Label(root, image=img)
        panel.image = img
        panel.pack()

    def create_label_buttons(self):
        for class_name in self.class_names:
            button = tk.Button(self.label_frame, text=class_name, command=lambda name=class_name: self.label_image(name))
            button.pack(side=tk.LEFT)

    def label_image(self, class_name):
        self.selected_class = class_name
        print("Image labeled with class:", self.selected_class)


class ImageProcessor:
    def __init__(self, camera_id=0):
        self.vid = cv2.VideoCapture(camera_id)
        #self.labler = labeling.ImageLabler()

    def capture_frame(self):
        self.vid.set(4, 720)
        self.vid.set(cv2.CAP_PROP_AUTOFOCUS, 0)
        ### КОСТЫЛЬ. КАМЕРА ФОКУСИРУЕТСЯ или что-то типа того
        _, frame = self.vid.read()
        _, frame = self.vid.read()
        _, frame = self.vid.read()
        _, frame = self.vid.read()
        _, frame = self.vid.read()
        _, frame = self.vid.read()
        _, frame = self.vid.read()
        _, frame = self.vid.read()
        _, frame = self.vid.read()
        ### КОСТЫЛЬ. КАМЕРА ФОКУСИРУЕТСЯ или что-то типа того
        frame = frame / 255
        self.release_camera()
        return frame

    @staticmethod
    def testDevice(camera_id):
        vid = cv2.VideoCapture(camera_id)
        if vid is None or not vid.isOpened():
            print('Warning: unable to open video source: ', vid)

    def select_objects(self):
        frame = self.capture_frame()
        rois = cv2.selectROIs("Select Rois", frame)
        return frame, rois

    def mark_objects(self, rois):
        frame = self.capture_frame()
        images = []
        for rect in rois:
            #x1 = rect[0]
            #y1 = rect[base_frame]
            #x2 = rect[2.jpg]
            #y2 = rect[3.jpg]
            #image = frame[y1: y1 + y2, x1: x1 + x2]
            image = frame
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            object = self.labler.label_image(image)
        return object

    def release_camera(self):
        self.vid.release()