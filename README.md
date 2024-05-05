# InpectVision
Software for monitoring device readings in real time by analyzing camera data.
![image.jpeg](Screenshots%2Fimage.jpeg)

The program takes an instrument panel as input and returns its “digital” representation

![result.png](Screenshots%2Fresult.jpeg)
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

Import everything you need

    from InpectVison import control_objects
    from InpectVison import objects_handler
    from InpectVison.processing import image_processing
    from InpectVison.data_logging import Notificator, TelegramApi

Run ImageProcessor to get regions of interest (roi)

    image_processor = image_processing.ImageProcessor(0)
    frame, rois = image_processor.select_objects()

It looks like:


![roi.jpeg](Screenshots%2Froi.jpeg)


Then create objects that you want to digitize. Now it can be bulbs or just number panels (including float numbers like 18.1).
Here You should point name, roi, init_value, frame and type. Type will be used in gui representation

        controlled_objects = []
        controlled_objects.append(
            control_objects.Bulb(name="Pumper_1", coordinates=rois[0],
                                      init_value=1, frame=frame, type=control_objects.ObjectsType.Binary)
        )
    
        controlled_objects.append(
            control_objects.Bulb(name="Pumper_2", coordinates=rois[1],
                                      init_value=0, frame=frame, type=control_objects.ObjectsType.Binary)
        )

Create monitor which will manage the objects digitizing

    monitor = objects_handler.Monitor(camera_id=0)

And run the run managing loop

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
