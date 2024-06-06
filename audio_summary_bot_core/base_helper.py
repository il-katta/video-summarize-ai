import logging
import os
import tempfile
from pathlib import Path
from typing import Optional

import whisper
from pydub import AudioSegment


class BaseHelper:
    _whisper_model: Optional[whisper.Whisper]
    _whisper_model_name: str
    _device: str
    _data_dir: Path

    def __init__(self, whisper_model_name: str = "large-v3", device: str = "cuda", data_dir: str | Path = "data"):
        self._whisper_model = None
        self._whisper_model_name = whisper_model_name
        self._device = device
        self._data_dir = Path(data_dir)

    def audio2text(
            self,
            file_content: bytes,
            initial_prompt: Optional[str] = None
    ) -> list[dict]:
        with tempfile.NamedTemporaryFile(suffix=f".wav") as tmp:
            tmp.write(file_content)
            tmp.flush()
            tmp.seek(0)
            # convert to wav
            sound = AudioSegment.from_file(tmp.name)
            sound.export(tmp.name, format="wav")
            result = self._get_whisper_model().transcribe(
                tmp.name,
                verbose=True,
                initial_prompt=initial_prompt,
                temperature=0.7,
                compression_ratio_threshold=1,
                condition_on_previous_text=True,
                # language=language,
                word_timestamps=True
            )
        return [{'start': s['start'], 'end': s['end'], 'text': s['text']} for s in result['segments']]

    def _get_whisper_model(self) -> whisper.Whisper:
        if self._whisper_model is None:
            logging.debug(f"Loading Whisper model using device {self._device}")
            self._whisper_model = whisper.load_model(
                self._whisper_model_name,
                download_root=str(self._data_dir),
                device=self._device
            )
        return self._whisper_model
