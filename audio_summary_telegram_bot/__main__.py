import argparse
import os
from pathlib import Path

from dotenv import load_dotenv

from audio_summary_telegram_bot.telegram_bot import TelegramBot


def main():
    load_dotenv()

    parser = argparse.ArgumentParser(description="telegram bot")
    parser.add_argument('--telegram-token', type=str, help="Telegram bot token")
    parser.add_argument('--data-dir', type=Path, default=Path('data'), help="data directory")
    parser.add_argument('--openai-model', type=str, help='OpenAI model', default='gpt-4o')
    parser.add_argument('--whisper-model', type=str, help='Whisper model', default='large-v3')
    parser.add_argument('--openai-api-key', type=str, help='OpenAI api key', default=None)
    parser.add_argument('--telegram-bot-api-server', type=str, help="telegram bot api server", default=None)
    args = parser.parse_args()

    openai_api_key = os.environ.get('OPENAI_API_KEY', args.openai_api_key)
    telegram_token = os.environ.get('TELEGRAM_TOKEN', args.telegram_token)
    bot = TelegramBot(
        token=telegram_token,
        telegram_bot_api_server=args.telegram_bot_api_server,
        openai_model=args.openai_model,
        whisper_model_name=args.whisper_model,
        openai_api_key=openai_api_key,
        data_dir=args.data_dir,
    )
    bot.start()


if __name__ == '__main__':
    main()
