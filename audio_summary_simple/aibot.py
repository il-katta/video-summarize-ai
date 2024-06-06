import json
import re
from pathlib import Path
from typing import List, Optional, Generator, TypedDict, Tuple

from openai import OpenAI
from openai.types.chat import ChatCompletionToolParam, ChatCompletionMessageToolCall

from audio_summary_bot_core.generic_helper import GenericHelper

PROMPT = """As a professional summarizer, your primary responsibility will be to create an organized summary of a video transcript segmented by topics.
The transcript provided will include timestamps for each sentence.
Your task entails compiling a comprehensive list of topics covered in the video along with a succinct summary for each topic.
It is imperative to accurately associate each topic with the corresponding timestamp from the transcript.
Precision and meticulous attention to detail in timestamp allocation are essential for the accuracy of the summary.
To begin, please review the video transcript and provide a detailed summary of the topics discussed along with their respective timestamps.
For each topic call the function add_topic with the topic, summary and timestamp as arguments.
Do not respond to this message, just call the function to save each topic.
"""


class TopicSummary(TypedDict):
    topic: str
    summary: str
    timestamp: Tuple[float, float]
    ref_url: Optional[str]


class AiBot:

    def __init__(
            self,
            openai_model: str = "gtp-4o",
            openai_api_key: Optional[str] = None,
            whisper_model_name: str = "large-v3",
            whisper_device: str = "cuda",
            data_dir: str | Path = "data"
    ):
        self._data_dir = data_dir
        self._openai_model = openai_model
        self._helper = GenericHelper(
            whisper_model_name=whisper_model_name,
            device=whisper_device,
            data_dir=data_dir
        )
        self._openai = OpenAI(api_key=openai_api_key)

    def summarize_video(self, video_url: str) -> Generator[TopicSummary, None, None]:
        if not self.validate_video_url(video_url):
            raise ValueError("Invalid video URL")
        video_id = self._helper.get_video_id(video_url)
        full_transcript = self.transcript_video(video_url)
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
        functions = {
            "add_topic": {
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
        responses = self._openai.chat.completions.create(
            model=self._openai_model,
            messages=messages,
            tools=tools,
            tool_choice="auto",
        )

        for response in responses.choices:
            response_message = response.message
            tool_calls: List[ChatCompletionMessageToolCall] = response_message.tool_calls
            if not tool_calls or len(tool_calls) == 0:
                raise RuntimeError("no tool calls found in response")
            for tool_call in tool_calls:
                fn_name = tool_call.function.name
                if fn_name not in functions.keys():
                    raise AttributeError(f"function '{fn_name}' not found in openai tools definitions")
                fn_args = json.loads(tool_call.function.arguments)
                fn_args['timestamp'] = tuple(fn_args['timestamp'])
                sec = int(fn_args['timestamp'][0])
                fn_args['ref_url'] = f'https://youtu.be/{video_id}?t={sec}s'
                yield fn_args

    def transcript_video(self, video_url: str) -> str:
        video_id = self._helper.get_video_id(video_url)
        audio_file = self._data_dir / f'{video_id}.webm'
        data_file = self._data_dir / f'{video_id}.json'

        if not audio_file.exists():
            audio_content = self._helper.video2audio(video_url)
            with audio_file.open('wb') as f:
                f.write(audio_content)
        else:
            with audio_file.open('rb') as f:
                audio_content = f.read()
        if not data_file.exists():
            transcript = self._helper.audio2text(audio_content)
            with data_file.open('w') as f:
                f.write(json.dumps(transcript))
        else:
            with data_file.open('r') as f:
                transcript = json.loads(f.read())

        full_transcript = "\n".join([f"[{s['start']} --> {s['end']}] {s['text']}" for s in transcript])
        return full_transcript

    def validate_video_url(self, video_url: str) -> bool:
        return self._helper.check_if_supported(video_url)
