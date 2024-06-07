import datetime
import logging
from typing import Generator, Tuple

from aiogram import types, enums
from aiogram.utils.text_decorations import HtmlDecoration

from video_summary_telegram_bot.filters import AllCommands


__all__ = ['OnMessageHandler']


class OnMessageHandler:
    def __init__(self, bot: 'video_summary_telegram_bot.telegram_bot.TelegramBot'):
        self.bot = bot

    async def __call__(self, message: types.Message):
        await self.on_message(message)

    async def on_message(self, message: types.Message) -> None:
        """on message"""
        logging.info(f"received a {message.content_type} message from {message.from_user.id}")
        try:
            await self._on_message(message)
        except Exception as e:
            logging.error(f"error on message from {message.from_user.id}: {e}")
            await message.reply("Sorry, an error occurred. Please try again later.")

    @property
    def filters(self):
        return [~AllCommands()]

    async def _on_message(self, message: types.Message) -> None:
        if message.content_type != enums.ContentType.TEXT:
            await message.reply("not supported")
            logging.info(f"{message.content_type} message from {message.from_user.id} is not supported")
            return
        message_text = message.text
        if not self.bot.ai.validate_video_url(message_text):
            await message.reply("url not supported")
            logging.info(f"message from {message.from_user.id} has an unsupported url: {message_text}")
            return
        logging.info(f"processing message from {message.from_user.id}: '{message_text}'")
        reply_message = await message.reply("processing ... please wait")

        for text, is_status in self._process_video_url(message_text):
            if is_status:
                await reply_message.edit_text(text)
            else:
                await self.bot.send_message_async(message.chat.id, text)

    def _process_video_url(self, video_url: str) -> Generator[Tuple[str, bool], None, None]:
        yield "processing: getting transcript ...", True
        transcript = self.bot.ai.transcript_video(video_url)

        yield "processing: summarizing ...", True
        summary = list(self.bot.ai.generate_summary(video_url, transcript))
        # sort by timestamp
        summary = sorted(summary, key=lambda x: x['timestamp'][0])

        yield "processing: complete", True
        for topic_id, d in enumerate(summary, start=1):
            yield self._format_response_text(d, topic_id), False

    @staticmethod
    def _format_response_text(d: dict, topic_id: int) -> str:
        _ = HtmlDecoration()
        title = _.bold(f"{topic_id} - {d['topic']}")
        if d['ref_url']:
            response_text = _.link(title, d['ref_url'])
        else:
            response_text = title
        response_text += _.blockquote(d['summary'])
        response_text += _.italic(
            f"{datetime.timedelta(seconds=int(d['timestamp'][0]))} - {datetime.timedelta(seconds=int(d['timestamp'][1]))}"
        )
        response_text += "\n"
        if d['ref_url']:
            response_text += _.link(d['ref_url'], d['ref_url'])
            response_text += "\n"
        return response_text
