# InpectVision - Software for monitoring device readings in real time by analyzing camera data.
![image.jpeg](Screenshots%2Fimage.jpeg)
The program takes an instrument panel as input and returns its “digital” representation
![result.png](Screenshots%2Fresult.png)
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

## Requirements
  - [Python (3.10+)]
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

    from InspectVision import gui, control_objects, objects_handler
    from InspectVision.processing import image_processing
    from InspectVision.data_logging import Notificator, TelegramApi

Run ImageProcessor that will handle your camera:

    image_processor = image_processing.ImageProcessor(0)

Select regions of interest (roi):

    frame, rois = image_processing.select_roi(image_processor)

It looks like:
![roi.jpeg](Screenshots%2Froi.jpeg)

Then create objects that you want to digitize. Now it can be bulbs or just number panels (including float numbers like 18.1).
Here You should point name, roi, init_value, frame and type. Type will be used in gui representation

        controlled_objects = []
        controlled_objects.append(
            control_objects.Bulb(name="bulb_1", coordinates=rois[0],
                                      init_value=1, frame=frame, gui_type=gui.WidgetType.Binary)
        )
    
        controlled_objects.append(
            control_objects.Bulb(name="bulb_2", coordinates=rois[1],
                                      init_value=0, frame=frame, gui_type=gui.WidgetType.Binary)
        )
To see all available gui types, you can just print it directly:

        print(gui.WidgetType)

Create monitor which will manage the objects digitizing

    monitor = objects_handler.Monitor(camera_id=0)

And run the run managing loop

    monitor = objects_handler.Monitor(image_processor)
    path = "data"
    monitor.run_loop(controlled_objects, show=True, telegram_api=None, log_path=path, log_every=2)

If you do everything right, You will see such screen:
![two_status_data.jpeg](Screenshots%2Ftwo_status_data.jpeg)

## TelegramApi and Notificator
You can create your own notifications. In the case of some Dangerous situation you will get message in Telegram.
To do this, import Base class Notificator and create its inheritor with method check_conditions

    from InpectVison.data_logging import Notificator

    class ChillerNotificator(Notificator):
        def check_conditions(self):
            condition = self.controlled_objects[0] > 17.8
            message = "The water temerature is hight!!!!!"
            return condition, message

And then in code create your notificator:

    notificator = ChillerNotificator(controlled_objects)

Then create your own telegram api:

    from InpectVison.data_logging import TelegramApi
    telegram_api = TelegramApi(token="some_toke_from_BotFather", notificator=notificator)

And the pass this to monitor:

    monitor.run_loop(controlled_objects, show=True, telegram_api=telegram_api, log_path=path, log_every=2)
    
## Available Panels
### Seven-segments number panels

![images](https://github.com/ArkadySamsonenkoWork/InspectVision/assets/153271915/6921fa36-3ab3-44bd-a2ba-4c1d28ec3410)

![hEzCp](https://github.com/ArkadySamsonenkoWork/InspectVision/assets/153271915/fb4ee765-4ab8-4286-bfa9-2562184d750b)

![865-00](https://github.com/ArkadySamsonenkoWork/InspectVision/assets/153271915/7bb54af8-577a-4c24-bdc6-1daafbdf47d7)

 ### Binary status bulbs

 ![bulb](https://github.com/ArkadySamsonenkoWork/InspectVision/assets/153271915/6f9cf3ed-d098-4565-a518-8a4f06905ba9)


## Writing Your Own Models
To write your own model you should create class inheritor from class control_objects

    from InspectVision.control_objects import ControlObject

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
