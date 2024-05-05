import aiogram
import typing as tp
from ..notification import Notificator
from aiogram import Bot, Dispatcher, executor, types

class TelegramApi:
    def __init__(self, token:str, notificator:Notificator):
        self.bot = Bot(token=token)
        self.notificator = notificator
        self.dp = Dispatcher(self.bot)
        self.users_collection = set()

    async def start(self, message: types.Message) -> None:
        user_id = message.from_user.id
        self.users_collection.add(user_id)
        await message.answer("I will add you in the users list")

    async def send_messages(self, text: str):
        for user_id in self.users_collection:
            await self.bot.send_message(user_id, text)

    async def update(self):
        text = self.notificator.aware()
        if not text:
            await self.send_messages(text)

    async def run(self) -> None:
        self.dp.register_message_handler(self.start, commands="start")
        # And the run events dispatching
        await executor.start_polling(self.dp, skip_updates=True)