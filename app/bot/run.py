"""Composition root for the Telegram adapter: builds the concrete
Transcriber/Summarizer and starts the bot.
"""
import asyncio

from aiogram import Bot, Dispatcher

from app.bot.handlers import build_router
from app.core.config import settings
from app.core.logging_config import setup_logging
from app.services.summarizer import GeminiSummarizer
from app.services.transcriber import WhisperTranscriber


async def start():
    transcriber = WhisperTranscriber(
        model_size=settings.whisper_model_size, language=settings.whisper_language
    )
    summarizer = GeminiSummarizer(
        api_key=settings.gemini_api_key,
        model=settings.gemini_model,
        language=settings.whisper_language,
        max_attempts=settings.gemini_max_attempts,
        retry_delay_seconds=settings.gemini_retry_delay_seconds,
    )

    bot = Bot(token=settings.telegram_token)
    dp = Dispatcher()
    dp.include_router(build_router(transcriber, summarizer))

    await dp.start_polling(bot)


if __name__ == "__main__":
    setup_logging()
    asyncio.run(start())
