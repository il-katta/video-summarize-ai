import asyncio
import datetime
import re
from pathlib import Path
from typing import Optional

from aiogram import Bot, Dispatcher
from aiogram import Router
from aiogram import enums
from aiogram import filters
from aiogram import types
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.telegram import TelegramAPIServer
from aiogram.fsm.storage.memory import SimpleEventIsolation
from aiogram.utils.text_decorations import HtmlDecoration

from audio_summary_simple.aibot import AiBot


class AllCommands(filters.Command):
    def __init__(self):
        super().__init__(re.compile(r".*"))


class TelegramBot:

    def __init__(
            self,
            token: str,
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
        self._router = Router()
        self._ai = AiBot(
            openai_model=openai_model,
            openai_api_key=openai_api_key,
            whisper_model_name=whisper_model_name,
            whisper_device=whisper_device,
            data_dir=data_dir
        )

    async def start_async(self) -> None:
        await self._register_handlers()
        await self._bot.delete_webhook()
        await self._dp.start_polling(self._bot)

    def start(self) -> None:
        task = self.start_async()
        asyncio.run(task, debug=True)

    async def _register_handlers(self) -> None:
        commands: list[types.BotCommand] = []
        for method_name in dir(self):
            if method_name.startswith("cmd_"):
                method = getattr(self, method_name)
                commands.append(types.BotCommand(command=method_name[4:], description=method.__doc__))
                if hasattr(method, "filters"):
                    _filters = method.filters
                else:
                    _filters = []
                self._dp.message.register(method, *_filters)
            if method_name.startswith("action_"):
                method = getattr(self, method_name)
                self._dp.callback_query.register(method, method.callback_query)
        self._router.message.register(self._on_message, ~AllCommands())
        self._dp.include_routers(self._router)
        await self._bot.delete_my_commands()
        await self._bot.set_my_commands(commands)

    async def cmd_start(self, message: types.Message) -> None:
        """Start command"""
        await message.reply("hello")

    async def _on_message(self, message: types.Message) -> None:
        if message.content_type != enums.ContentType.TEXT:
            await message.reply("not supported")
            return
        message_text = message.text
        if not self._ai.validate_video_url(message_text):
            await message.reply("url not supported")
            return
        reply_message = await message.reply("processing ... please wait")
        summary = self._ai.summarize_video(message_text)
        topic_id = 0
        for d in summary:
            if topic_id == 0:
                await self.edit_message_text_async("Process complete",
                                                   chat_id=reply_message.chat.id,
                                                   message_id=reply_message.message_id)
            topic_id += 1
            title = self._.bold(f"{topic_id} - {d['topic']}")
            if d['ref_url']:
                response_text = self._.link(title, d['ref_url'])
            else:
                response_text = title
            response_text += self._.blockquote(d['summary'])
            if d['ref_url']:
                response_text += self._.link(d['ref_url'], d['ref_url'])
            response_text += self._.italic(f"{datetime.timedelta(seconds=int(d['timestamp'][0]))} - {datetime.timedelta(seconds=int(d['timestamp'][1]))}")
            await self.send_message_async(chat_id=reply_message.chat.id, text=response_text)

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
