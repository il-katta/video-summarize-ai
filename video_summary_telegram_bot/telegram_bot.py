import asyncio
import logging
from pathlib import Path
from typing import Optional

from aiogram import Bot, Dispatcher
from aiogram import enums
from aiogram import filters
from aiogram import types
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.telegram import TelegramAPIServer
from aiogram.fsm.storage.memory import SimpleEventIsolation
from aiogram.utils.text_decorations import HtmlDecoration
from video_summary_simple.aibot import AiBot
from video_summary_telegram_bot.handlers.on_message_handler import OnMessageHandler


class TelegramBot:

    def __init__(
            self,
            token: str,
            summary_language: Optional[str] = None,
            telegram_bot_api_server: Optional[str] = None,
            openai_model: str = "gtp-4o",
            openai_api_key: Optional[str] = None,
            whisper_model_name: str = "large-v3",
            whisper_device: str = "cuda",
            data_dir: str | Path = "data"
    ):
        self._telegram_bot_api_server = telegram_bot_api_server
        if self._telegram_bot_api_server:
            session = AiohttpSession(api=TelegramAPIServer.from_base(self._telegram_bot_api_server, is_local=True))
        else:
            session = None
        self._dp = Dispatcher(
            events_isolation=SimpleEventIsolation(),
        )
        self._bot = Bot(token=token, parse_mode=enums.ParseMode.HTML, session=session)
        self._ = HtmlDecoration()
        self._loop = asyncio.get_event_loop()
        self._ai = AiBot(
            language=summary_language,
            openai_model=openai_model,
            openai_api_key=openai_api_key,
            whisper_model_name=whisper_model_name,
            whisper_device=whisper_device,
            data_dir=data_dir
        )

    async def start_async(self) -> None:
        logging.info("starting bot")
        await self._register_handlers()
        await self._bot.delete_webhook()
        await self._dp.start_polling(self._bot)

    def start(self) -> None:
        task = self.start_async()
        asyncio.run(task, debug=True)

    async def _register_handlers(self) -> None:
        commands: list[types.BotCommand] = []
        for method_name in dir(self):
            # register all command methods
            if method_name.startswith("cmd_"):
                method = getattr(self, method_name)
                commands.append(types.BotCommand(command=method_name[4:], description=method.__doc__))
                if hasattr(method, "filters"):
                    self._dp.message.register(method, *method.filters)
                else:
                    self._dp.message.register(method)

            # register all action methods
            if method_name.startswith("action_"):
                method = getattr(self, method_name)
                self._dp.callback_query.register(method, method.callback_query)

        # default message handler
        handler = OnMessageHandler(self)
        self._dp.message.register(handler.on_message, *handler.filters)

        # refresh commands list
        await self._bot.delete_my_commands()
        await self._bot.set_my_commands(commands)

    async def cmd_start(self, message: types.Message) -> None:
        """Start command"""
        logging.info(f"received a start command from {message.from_user.id}")
        await message.reply("hello")

    cmd_start.filters = [filters.CommandStart()]

    async def edit_message_text_async(self, text: str, chat_id: int, message_id: int, *args, **kwargs) -> types.Message:
        return await self._bot.edit_message_text(text, chat_id=chat_id, message_id=message_id, *args, **kwargs)

    async def send_message_async(self, chat_id: int, text: str, reply_to_message_id: int = None) -> types.Message:
        return await self._bot.send_message(chat_id,
                                            text,
                                            reply_to_message_id=reply_to_message_id,
                                            link_preview_options=types.LinkPreviewOptions(is_disabled=True),
                                            parse_mode=enums.ParseMode.HTML
                                            )

    @property
    def ai(self) -> AiBot:
        return self._ai
