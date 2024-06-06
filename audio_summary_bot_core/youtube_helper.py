import os
import re
import tempfile
from typing import Optional

import yt_dlp

from audio_summary_bot_core.base_helper import BaseHelper


class YoutubeHelper(BaseHelper):

    @staticmethod
    def video2audio(video_url: str) -> bytes:
        with tempfile.TemporaryDirectory() as tmp_dir:
            ydl_opts = {
                'format': 'bestaudio/best',
                ## 'writesubtitles': True,
                # 'writeautomaticsub': True,
                'subtitleslangs': ['it'],
                'sponsorblock_remove': ['sponsor'],
                # 'subtitlesformat': 'srt',
                'outtmpl': {
                    'default': f"{tmp_dir}/audio.%(ext)s",
                }
            }

            file_name = None
            srt_file_name = None
            try:

                ydl = yt_dlp.YoutubeDL(ydl_opts)
                ydl.download([video_url])
                if len(os.listdir(tmp_dir)) > 1:
                    try:
                        srt_file_name = os.path.join(tmp_dir, [
                            f for f in os.listdir(tmp_dir)
                            if f.lower().endswith('.vtt') or f.lower().endswith('.srt')
                        ][0])
                    except IndexError:
                        srt_file_name = None
                    file_name = os.path.join(tmp_dir, [
                        f for f in os.listdir(tmp_dir)
                        if f.lower().endswith('.mp4') or
                           f.lower().endswith('.webm') or
                           f.lower().endswith('.m4a') or
                           f.lower().endswith('.ogg') or
                           f.lower().endswith('.opus')
                    ][0])
                else:
                    srt_file_name = None
                    file_name = os.path.join(tmp_dir, os.listdir(tmp_dir)[0])
                with open(file_name, "rb") as f:
                    content = f.read()
                os.remove(file_name)
                # subtitle is ignored for now
                # return the file audio content
                return content
            finally:
                if file_name and os.path.exists(file_name):
                    os.remove(file_name)
                if srt_file_name and os.path.exists(srt_file_name):
                    os.remove(srt_file_name)

    def video2text(self, video_url: str) -> list[dict]:
        audio_content = self.video2audio(video_url)
        return self.audio2text(audio_content)

    def get_video_id(self, video_url: str) -> Optional[str]:
        youtube_regex = (
            r'(https?://)?(www\.)?'
            '(youtube|youtu|youtube-nocookie)\.(com|be)/'
            '(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})'
        )
        youtube_regex_match = re.search(youtube_regex, video_url)
        if youtube_regex_match:
            return youtube_regex_match.group(6)
        else:
            return None
