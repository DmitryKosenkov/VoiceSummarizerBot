"""Telegram message handlers. The only file in the project that knows
about Telegram/aiogram; everything else goes through app/pipeline.py.
"""
import asyncio
import logging
import os
from pathlib import Path

from aiogram import F, Router, types
from aiogram.filters import Command, CommandStart

from app.bot import messages, summary_cache, transcript_cache
from app.core.config import settings
from app.pipeline import TranscriptionError, summarize_async, transcribe_async
from app.services.summarizer import Summarizer, SummarizationError
from app.services.transcriber import Transcriber
from exporters.docx_export import render_markdown_summary_to_docx
from exporters.txt_export import render_transcript_to_txt

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {".mp3", ".wav", ".ogg", ".m4a", ".flac", ".webm", ".opus", ".aac"}


def build_router(transcriber: Transcriber, summarizer: Summarizer) -> Router:
    router = Router()
    os.makedirs(settings.downloads_dir, exist_ok=True)

    @router.message(CommandStart())
    async def start_command(message: types.Message):
        await message.answer(messages.WELCOME.format(name=message.from_user.first_name))

    @router.message(Command("retry"))
    async def retry_command(message: types.Message):
        text = transcript_cache.get(message.from_user.id)
        if not text:
            await message.answer(messages.NOTHING_TO_RETRY)
            return
        await message.answer(messages.GENERATING_SUMMARY)
        await reply_with_summary(message, text, summarizer)

    @router.message(Command("docx"))
    async def docx_command(message: types.Message):
        summary = summary_cache.get(message.from_user.id)
        if not summary:
            await message.answer(messages.NOTHING_TO_EXPORT)
            return
        await send_summary_as_docx(message, summary)

    @router.message(Command("txt"))
    async def txt_command(message: types.Message):
        text = transcript_cache.get(message.from_user.id)
        if not text:
            await message.answer(messages.NOTHING_TO_EXPORT_TXT)
            return
        await send_transcript_as_txt(message, text)

    @router.message(F.voice)
    async def handle_voice(message: types.Message):
        await handle_incoming_audio(message, message.voice, ".ogg", transcriber, summarizer)

    @router.message(F.audio)
    async def handle_audio(message: types.Message):
        extension = _extension_of(message.audio.file_name) or ".mp3"
        if extension not in ALLOWED_EXTENSIONS:
            return await message.answer(_unsupported_format_message())
        await handle_incoming_audio(message, message.audio, extension, transcriber, summarizer)

    @router.message(F.document)
    async def handle_document(message: types.Message):
        extension = _extension_of(message.document.file_name)
        if extension not in ALLOWED_EXTENSIONS:
            return await message.answer(_unsupported_format_message())
        await handle_incoming_audio(message, message.document, extension, transcriber, summarizer)

    return router


def _extension_of(file_name: str | None) -> str:
    return Path(file_name).suffix.lower() if file_name else ""


def _unsupported_format_message() -> str:
    formats = ", ".join(sorted(ALLOWED_EXTENSIONS))
    return messages.UNSUPPORTED_FORMAT.format(formats=formats)


async def handle_incoming_audio(
    message: types.Message,
    file_obj,
    extension: str,
    transcriber: Transcriber,
    summarizer: Summarizer,
) -> None:
    await message.answer(messages.FILE_RECEIVED)

    local_path = None
    try:
        local_path = await download_audio(message, file_obj, extension)
        await message.answer(messages.FILE_DOWNLOADED)

        text = await transcribe_async(local_path, transcriber)
        transcript_cache.store(message.from_user.id, text)
        await send_transcript_as_txt(message, text)

        await message.answer(messages.GENERATING_SUMMARY)
        await reply_with_summary(message, text, summarizer)

    except TranscriptionError:
        await message.answer(messages.TRANSCRIPTION_FAILED)

    except Exception:
        logger.exception(
            "Unexpected error while processing a file for user %s", message.from_user.id
        )
        await message.answer(messages.UNEXPECTED_ERROR)

    finally:
        if local_path and os.path.exists(local_path):
            os.remove(local_path)


async def download_audio(message: types.Message, file_obj, extension: str) -> str:
    local_path = f"{settings.downloads_dir}/{file_obj.file_id}{extension}"
    file_info = await message.bot.get_file(file_obj.file_id)
    await message.bot.download_file(file_path=file_info.file_path, destination=local_path)
    return local_path


async def reply_with_summary(message: types.Message, text: str, summarizer: Summarizer) -> None:
    try:
        summary = await summarize_async(text, summarizer)
    except SummarizationError:
        logger.error("Summarization failed for user %s", message.from_user.id)
        await message.answer(messages.SUMMARY_FAILED)
        return

    transcript_cache.clear(message.from_user.id)
    summary_cache.store(message.from_user.id, summary)
    await send_summary_as_docx(message, summary)
    await message.answer(messages.FILES_AVAILABLE_AGAIN_HINT)


async def send_summary_as_docx(message: types.Message, summary_markdown: str) -> None:
    loop = asyncio.get_running_loop()
    docx_bytes = await loop.run_in_executor(
        None, render_markdown_summary_to_docx, summary_markdown
    )
    document = types.BufferedInputFile(docx_bytes, filename=messages.DOCX_FILENAME)
    await message.answer_document(document=document, caption=messages.DOCX_CAPTION)


async def send_transcript_as_txt(message: types.Message, transcript: str) -> None:
    txt_bytes = render_transcript_to_txt(transcript)
    document = types.BufferedInputFile(txt_bytes, filename=messages.TXT_FILENAME)
    await message.answer_document(document=document, caption=messages.TXT_CAPTION)
