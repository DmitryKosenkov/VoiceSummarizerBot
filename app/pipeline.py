"""Core transcribe-then-summarize logic. Delivery-agnostic: no Telegram or
web-framework imports, so any adapter can call these functions directly.
"""
import asyncio

from app.services.summarizer import Summarizer
from app.services.transcriber import Transcriber


class TranscriptionError(Exception):
    """Raised when no speech could be recognized in the audio file."""


def transcribe(audio_path: str, transcriber: Transcriber) -> str:
    text = transcriber.transcribe(audio_path)
    if not text:
        raise TranscriptionError("No speech could be recognized in this file.")
    return text


def summarize(text: str, summarizer: Summarizer) -> str:
    return summarizer.summarize(text)


def transcribe_and_summarize(
    audio_path: str, transcriber: Transcriber, summarizer: Summarizer
) -> tuple[str, str]:
    """Run both steps at once. Callers that need to handle a partial
    (transcript-only) success should call transcribe() and summarize()
    separately instead.
    """
    text = transcribe(audio_path, transcriber)
    summary = summarize(text, summarizer)
    return text, summary


async def transcribe_async(audio_path: str, transcriber: Transcriber) -> str:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, transcribe, audio_path, transcriber)


async def summarize_async(text: str, summarizer: Summarizer) -> str:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, summarize, text, summarizer)
