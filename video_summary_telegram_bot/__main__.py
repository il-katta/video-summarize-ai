import argparse
import os
from pathlib import Path
import logging
from dotenv import load_dotenv

from video_summary_telegram_bot.telegram_bot import TelegramBot


def main():
    load_dotenv()



    parser = argparse.ArgumentParser(description="telegram bot")
    parser.add_argument('--telegram-token', type=str, help="Telegram bot token")
    parser.add_argument('--data-dir', type=Path, help="data directory",
                        default=Path(os.environ.get('DATA_DIR', 'data')))
    parser.add_argument('--openai-model', type=str, help='OpenAI model',
                        default=os.environ.get('OPENAI_MODEL', 'gpt-4o'))
    parser.add_argument('--whisper-model', type=str, help='Whisper model',
                        default=os.environ.get('WHISPER_MODEL', 'large-v3'))
    parser.add_argument('--openai-api-key', type=str, help='OpenAI api key', default=None)
    parser.add_argument('--telegram-bot-api-server', type=str, help="telegram bot api server", default=None)
    parser.add_argument('--language', type=str, help="summary language", default=None)

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    openai_api_key = args.openai_api_key or os.environ.get('OPENAI_API_KEY', None)
    telegram_token = args.telegram_token or os.environ.get('TELEGRAM_TOKEN', None)
    summary_language = args.language or os.environ.get('SUMMARY_LANGUAGE', None)
    telegram_bot_api_server = args.telegram_bot_api_server or os.environ.get('TELEGRAM_BOT_API_SERVER', None)
    openai_model = args.openai_model
    whisper_model = args.whisper_model
    data_dir = args.data_dir
    bot = TelegramBot(
        token=telegram_token,
        summary_language=summary_language,
        telegram_bot_api_server=telegram_bot_api_server,
        openai_model=openai_model,
        whisper_model_name=whisper_model,
        openai_api_key=openai_api_key,
        data_dir=data_dir,
    )
    bot.start()


if __name__ == '__main__':
    main()
