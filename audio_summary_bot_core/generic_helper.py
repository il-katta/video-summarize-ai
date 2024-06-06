import os
import tempfile
from typing import Optional

import yt_dlp


from audio_summary_bot_core.base_helper import BaseHelper





class GenericHelper(BaseHelper):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._yt = yt_dlp.YoutubeDL()

    def video2audio(self, video_url: str) -> bytes:
        with tempfile.TemporaryDirectory() as tmp_dir:
            ydl_opts = {
                'format': 'bestaudio/best',
                'sponsorblock_remove': ['sponsor'],
                'outtmpl': {
                    'default': f"{tmp_dir}/audio.%(ext)s",
                }
            }
            file_name = None
            try:
                self._yt.params.update(ydl_opts)
                self._yt.download([video_url])
                if len(os.listdir(tmp_dir)) > 1:
                    fn = [
                        f for f in os.listdir(tmp_dir)
                        if f.lower().endswith('.mp4') or
                           f.lower().endswith('.webm') or
                           f.lower().endswith('.m4a') or
                           f.lower().endswith('.ogg') or
                           f.lower().endswith('.opus')
                    ][0]
                    file_name = os.path.join(tmp_dir, fn)
                else:
                    file_name = os.path.join(tmp_dir, os.listdir(tmp_dir)[0])
                with open(file_name, "rb") as f:
                    content = f.read()
                os.remove(file_name)
                return content
            finally:
                if file_name and os.path.exists(file_name):
                    os.remove(file_name)

    def video2text(self, video_url: str) -> list[dict]:
        audio_content = self.video2audio(video_url)
        return self.audio2text(audio_content)

    @staticmethod
    def _check_if_supported( url: str) -> bool:
        for ie in yt_dlp.list_extractors():
            if ie.suitable(url):
                return True
        return False

    def check_if_supported(self, url: str) -> bool:
        if not self._check_if_supported(url):
            return False
        try:
            info = self._yt.extract_info(url, download=False)
            return bool(info.get('extractor'))
        except yt_dlp.DownloadError:
            return False

    def is_youtube_video(self, url: str) -> bool:
        import yt_dlp.extractor.youtube
        return yt_dlp.extractor.youtube.YoutubeIE().suitable(url)

    def get_video_id(self, url: str) -> Optional[str]:
        try:
            info = self._yt.extract_info(url, download=False)
            return info.get('id')
        except yt_dlp.DownloadError:
            return None
