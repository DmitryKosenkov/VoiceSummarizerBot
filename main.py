"""Entry point. Starts the Telegram bot."""
import asyncio

from app.bot.run import start
from app.core.logging_config import setup_logging

if __name__ == "__main__":
    setup_logging()
    asyncio.run(start())
