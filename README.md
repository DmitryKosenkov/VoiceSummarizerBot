# WhisperBot

A Telegram bot that transcribes voice messages and audio files using
[faster-whisper](https://github.com/SYSTRAN/faster-whisper) and generates a
summary with Google Gemini.

## Features

- Accepts Telegram voice messages and audio/document uploads (`.mp3`, `.wav`,
  `.ogg`, `.m4a`, `.flac`, `.webm`, `.opus`, `.aac`)
- Local, offline transcription via faster-whisper
- Summary generation via Gemini, with automatic retry on transient API errors
- `/retry` re-generates a summary from the cached transcript without
  re-uploading the audio

## Project layout

```
main.py                    entry point

app/
  core/
    config.py               settings, loaded from .env
    logging_config.py       logging setup

  services/
    transcriber.py          Transcriber interface + WhisperTranscriber
    summarizer.py           Summarizer interface + GeminiSummarizer
    prompts.py               Gemini prompt template

  pipeline.py                transcribe() / summarize() - delivery-agnostic
                              core logic

  bot/
    handlers.py              Telegram message handlers
    messages.py               user-facing text
    transcript_cache.py       per-user transcript cache, used by /retry
    run.py                   builds and starts the bot

  utils/
    text_utils.py             chunk_text() helper
```

## Architecture

`Transcriber` and `Summarizer` are abstract interfaces with a single method
each (Strategy pattern). `WhisperTranscriber` and `GeminiSummarizer` are the
current implementations; swapping either provider means adding one class in
`app/services/` and updating `app/bot/run.py`.

`app/pipeline.py` contains the actual transcribe/summarize logic and has no
dependency on Telegram or aiogram. `app/bot/handlers.py` calls into it and
handles only Telegram-specific concerns (message formatting, file download,
chunking). This keeps the delivery channel swappable - e.g. a FastAPI
adapter could call the same pipeline functions from an HTTP route without
any changes to `app/pipeline.py` or `app/services/`.

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env   # fill in TOKEN and GEMINI_API_KEY
python main.py
```

## Configuration

All settings are read from environment variables (see `.env.example`):

| Variable                     | Default              | Description                          |
|-------------------------------|-----------------------|---------------------------------------|
| `TOKEN`                      | -                     | Telegram bot token                   |
| `GEMINI_API_KEY`             | -                     | Gemini API key                       |
| `WHISPER_MODEL_SIZE`         | `large-v3-turbo`      | faster-whisper model size            |
| `WHISPER_LANGUAGE`           | `ru`                  | Language passed to Whisper           |
| `GEMINI_MODEL`               | `gemini-3.5-flash`    | Gemini model used for summarization  |
| `GEMINI_MAX_ATTEMPTS`        | `3`                   | Retry attempts on transient errors   |
| `GEMINI_RETRY_DELAY_SECONDS` | `5`                   | Base delay between retries           |
| `DOWNLOADS_DIR`               | `downloads`           | Local directory for downloaded audio |

