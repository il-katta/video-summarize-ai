import json
import os
import re
from pathlib import Path
from typing import Tuple, List

from openai.types.chat import ChatCompletionToolParam, ChatCompletionMessageToolCall

from audio_summary_bot_core.youtube_helper import YoutubeHelper

PROMPT = """As a professional summarizer, your primary responsibility will be to create an organized summary of a video transcript segmented by topics.
The transcript provided will include timestamps for each sentence.
Your task entails compiling a comprehensive list of topics covered in the video along with a succinct summary for each topic.
It is imperative to accurately associate each topic with the corresponding timestamp from the transcript.
Precision and meticulous attention to detail in timestamp allocation are essential for the accuracy of the summary.
To begin, please review the video transcript and provide a detailed summary of the topics discussed along with their respective timestamps.
For each topic call the function add_topic with the topic, summary and timestamp as arguments.
Do not respond to this message, just call the function to save each topic.
"""

from openai import OpenAI

from dotenv import load_dotenv

load_dotenv()


def add_topic(topic: str, summary: str, timestamp: Tuple[float, float]) -> bool:
    print(f"topic: {topic} - summary: {summary} - timestamp: {timestamp}")
    return True


functions = {
    "add_topic": {
        "fn": add_topic,
        "description": "function for storing topics with summaries",
        "parameters": {
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "description": "Title of the topic",
                },
                "summary": {"type": "string", "description": "Summary of the topic"},
                "timestamp": {
                    "type": "array",
                    "description": "Timestamp of the topic in a tuple with [start, end]",
                    "items": {
                        "type": "number"
                    }
                }
            },
            "required": ["topic", "summary", "timestamp"],
        }
    }
}


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Simple script to summarize a Youtube video")
    parser.add_argument("video_url", help="Youtube video url to be summarized")
    parser.add_argument('--data-dir', type=Path, default=Path('data'), help="data directory")
    args = parser.parse_args()
    youtube_video_url = args.video_url
    data_dir: Path = args.data_dir
    data_dir.mkdir(exist_ok=True, parents=True)
    helper = YoutubeHelper(data_dir=data_dir)
    #video_id = re.search(r"v=([^&]+)", youtube_video_url).group(1)
    video_id = helper.get_video_id(youtube_video_url)
    if not video_id:
        raise Exception("video url not valid")

    if not (data_dir / f'{video_id}.webm').exists():
        audio_content = helper.video2audio(youtube_video_url)
        with open(data_dir / f'{video_id}.webm', 'wb') as f:
            f.write(audio_content)
    else:
        with open(data_dir / f'{video_id}.webm', 'rb') as f:
            audio_content = f.read()
    if not (data_dir / f'{video_id}.json').exists():
        transcript = helper.audio2text(audio_content)
        with open(data_dir / f'{video_id}.json', 'w') as f:
            f.write(json.dumps(transcript))
    else:
        with open(data_dir / f'{video_id}.json', 'r') as f:
            transcript = json.loads(f.read())
    full_transcript = "\n".join([f"[{s['start']} --> {s['end']}] {s['text']}" for s in transcript])
    client = OpenAI(
        api_key=os.environ.get("OPENAI_API_KEY", None)
    )

    messages = [
        {
            "role": "system",
            "content": PROMPT,
        },
        {
            "role": "system",
            "content": f"This is the video transcript with timestamps:\n\n{full_transcript}"
        }
    ]

    tools: List[ChatCompletionToolParam] = [
        {
            "type": "function",
            "function": {
                "name": fn_name,
                "description": fn_info["description"],
                "parameters": fn_info["parameters"],
            }
        }
        for fn_name, fn_info in functions.items()
    ]
    responses = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        tools=tools,
        tool_choice="auto",
    )
    for response in responses.choices:
        response_message = response.message
        tool_calls: List[ChatCompletionMessageToolCall] = response_message.tool_calls
        # if not tool_calls or len(tool_calls) == 0:
        #    raise RuntimeError("no tool calls found in response")
        for tool_call in tool_calls:
            fn_name = tool_call.function.name
            if fn_name not in functions.keys():
                raise AttributeError(f"function '{fn_name}' not found in openai tools definitions")
            fn_args = json.loads(tool_call.function.arguments)
            sec = int(fn_args['timestamp'][0])
            print("")
            print(f"# {fn_args['topic']}")
            print()
            print(f"[link](https://youtu.be/{video_id}?t={sec}s)")
            print("")
            print(fn_args['summary'])
            print("")
            print("")


if __name__ == '__main__':
    main()
