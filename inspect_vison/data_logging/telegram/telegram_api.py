import typing as tp
import telebot

import threading

from ..notification import Notificator

class TelegramBot:
    def __init__(self, token:str, notificator:Notificator):
        self.bot = telebot.TeleBot(token=token)
        self.notificator = notificator
        self.users_collection = set()
        #self.dp.middleware.setup(LoggingMiddleware())

    def start(self, message) -> None:
        user_id = message.from_user.id
        self.users_collection.add(user_id)
        self.bot.send_message(user_id, "I will add you in the users list")

    def send_messages(self, text: str):
        for user_id in self.users_collection:
            self.bot.send_message(user_id, text)

    def update(self, update_values: dict[str, tp.Any]):
        self.notificator.update(update_values)
        text = self.notificator.aware()
        if text:
            self.send_messages(text)

    def start_polling(self):
        self.bot.register_message_handler(self.start, commands=["start"])
        self.bot.polling(none_stop=True, interval=0)


class TelegramApi:
    def __init__(self, token:str, notificator:Notificator):
        self.bot = TelegramBot(token, notificator)

    def run(self) -> None:
        thread = threading.Thread(target=self.bot.start_polling, args=())
        thread.start()

    def update(self, update_values: dict[str, tp.Any]):
        self.bot.update(update_values)


if __name__ == "__main__":
    pass