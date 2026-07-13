import logging
from abc import ABC, abstractmethod

from faster_whisper import WhisperModel

logger = logging.getLogger(__name__)


class Transcriber(ABC):
    """Converts an audio file into text."""

    @abstractmethod
    def transcribe(self, audio_path: str) -> str:
        raise NotImplementedError


class WhisperTranscriber(Transcriber):
    """Local speech-to-text using faster-whisper."""

    def __init__(self, model_size: str = "large-v3-turbo", language: str = "ru"):
        logger.info("Loading Whisper model '%s'...", model_size)
        self.model = WhisperModel(model_size, device="cpu", compute_type="int8")
        self.language = language
        logger.info("Whisper model loaded.")

    def transcribe(self, audio_path: str) -> str:
        try:
            segments, _info = self.model.transcribe(
                audio_path, language=self.language, beam_size=5
            )
            return " ".join(segment.text.strip() for segment in segments).strip()
        except Exception:
            logger.exception("Whisper failed to process %s", audio_path)
            raise
