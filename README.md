# InpectVision - Software for monitoring device readings in real time by analyzing camera data.
![image.jpeg](Screenshots%2Fimage.jpeg)

The program takes an instrument panel as input and returns its “digital” representation

![result.png](Screenshots%2Fresult._upd.jpeg)


## Contents
  - [Requirements]
  - [Basic usage]
  - [Notification]
  - [TelegramApi and Notificator]
  - [Available Panels]
     - [Seven-segments number panels]
     - [Binary status bulbs]
  - [Available GUI Representation]
     - [Plots]
     - [LCDS number]
     - [Binary Status]
  - [Writing Own Models]
  - [Warning]

## Requirements
  - [Python (3.9+)]
  - [OnnxRuntime] for running natural network models 
  - [OpenCV]
  - [Numpy]
  - [PyQt6]
  - [Aiogram] for running telegram bots 
  - [Pyqtgraph] 

## Basic usage

Install from the source directory:

	pip3 install -e .

Import everything you need:

    from inspect_vision import gui, handlers, managing
    from inspect_vision.processing import image_processing
    from inspect_vision.data_logging import Notificator, TelegramApi

Run ImageProcessor that will handle your camera:

    image_processor = image_processing.ImageProcessor(0)

Select regions of interest (roi):

    frame, rois = image_processing.select_roi(image_processor)

It looks like:


![roi.jpeg](Screenshots%2Froi.jpeg)


Then create objects that you want to digitize. Now it can be bulbs or just number panels (including float numbers like 18.1).
Here, you should point name, roi, init_value, frame and type. Type will be used in gui representation.

        controlled_objects = []
        controlled_objects.append(
            handlers.Bulb(name="bulb_1", coordinates=rois[0],
                                      init_value=1, frame=frame, gui_type=gui.WidgetType.Binary)
        )
    
        controlled_objects.append(
            handlers.Bulb(name="bulb_2", coordinates=rois[1],
                                      init_value=0, frame=frame, gui_type=gui.WidgetType.Binary)
        )
	
To see all available gui types, you can just print it directly:

        print(gui.WidgetType)

Create monitor which manages the objects digitizing

    monitor = managing.Monitor(image_processor))

And run the loop.

    path = "data"
    monitor.run_loop(controlled_objects, show=True, telegram_api=None, log_path=path, log_every=2)

If you do everything right, You will see such screen:


![two_status_data.jpeg](Screenshots%2Ftwo_status_data.jpeg)



## TelegramApi and Notificator
You can create your own notifications. In the case of some dangerous situation you will get message in Telegram.
To do this, import Base class Notificator and create its sublass with method check_conditions

    from inspect_vision.data_logging import Notificator

    class ChillerNotificator(Notificator):
        def check_conditions(self):
            condition = self.controlled_objects["high_temperature_detector"] > 17.8
            message = "The water temerature is too hight!!!!!"
            return condition, message

And then in code create your notificator:

    notificator = ChillerNotificator(controlled_objects)

Then create your own telegram api:

    from inspect_vision.data_logging import TelegramApi
    telegram_api = TelegramApi(token="some_toke_from_BotFather", notificator=notificator)

And pass this to monitor:

    monitor.run_loop(controlled_objects, show=True, telegram_api=telegram_api, log_path=path, log_every=2)
    
## Available Panels
### Seven-segments number panels


![digits_display](https://github.com/ArkadySamsonenkoWork/InspectVision/assets/153271915/319324e2-444d-42e6-9c90-261a983b49a9)


 ### Binary status bulbs


![bulbs](https://github.com/ArkadySamsonenkoWork/InspectVision/assets/153271915/c2b67c9e-7f32-4125-9c42-121ac69259b4)


## Writing Your Own Models
To write your own model you should create class inheritor from class control_objects

    from inspect_vision.handlers import ControlObject

Then create subclass with one or two methods:

    class SomeObject(ControlObject):
        def _init_model(self):
            your_own_model = YOUR_MODEL(self.init_value, self.init_image)
            return your_own_model

        def check_gui_type(self):
            if self.gui_type is not gui.WidgetType.Binary:
                warnings.warn("Git type for bulb must be Binary")

The method _init_model is necessary. It returns model with method __call__ that takes image of detector and return value from it.
The method check_gui_type is not necessary. it checks the right usage of gui_type

## Warning

Unfortunately, some models are too large to fit into the github. However, you can download them from the link https://disk.yandex.ru/d/XPGHO5yS6oGRDA
