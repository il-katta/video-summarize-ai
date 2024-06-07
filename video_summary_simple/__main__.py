import argparse
import os
from pathlib import Path

from video_summary_simple.aibot import AiBot


def main():
    parser = argparse.ArgumentParser(description="Simple script to summarize a Youtube video")
    parser.add_argument("video_url", help="Youtube video url to be summarized")
    parser.add_argument('--data-dir', type=Path, default=Path('data'), help="data directory")
    parser.add_argument('--openai-model', type=str, help='OpenAI model', default='gpt-4o')
    parser.add_argument('--whisper-model', type=str, help='Whisper model', default='large-v3')
    parser.add_argument('--openai-api-key', type=str, help='OpenAI api key', default=None)
    args = parser.parse_args()
    youtube_video_url = args.video_url
    data_dir: Path = args.data_dir
    data_dir.mkdir(exist_ok=True, parents=True)
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', args.openai_api_key)
    ai = AiBot(
        data_dir=data_dir,
        openai_model=args.openai_model,
        whisper_model_name=args.whisper_model,
        openai_api_key=OPENAI_API_KEY
    )

    for d in ai.summarize_youtube_video(youtube_video_url):
        print("")
        print(f"# {d['topic']}")
        print("")
        print(f"[link]({d['ref_url']})")
        print("")
        print(d['summary'])
        print("")


if __name__ == '__main__':
    main()
