# WhisperBot

A Telegram bot that transcribes voice messages and audio files using
[faster-whisper](https://github.com/SYSTRAN/faster-whisper) and generates a
summary with Google Gemini.

## Features

- Accepts Telegram voice messages and audio/document uploads (`.mp3`, `.wav`,
  `.ogg`, `.m4a`, `.flac`, `.webm`, `.opus`, `.aac`)
- Local, offline transcription via faster-whisper
- Summary generation via Gemini, with automatic retry on transient API errors
- Delivers the transcript as a `.txt` file and the summary as a `.docx` file
- `/retry` re-generates a summary from the cached transcript without
  re-uploading the audio

## Project layout

```
main.py                     entry point

app/
  exporters/                 standalone converters, no import from app.bot
    docx_export/               Markdown -> Word converter (needs python-docx)
      converter.py
      __main__.py                 CLI: python -m app.exporters.docx_export input.md output.docx
    txt_export/                 transcript -> .txt converter (stdlib only)
      converter.py
      __main__.py                 CLI: python -m app.exporters.txt_export input.txt output.txt

  core/
    config.py                settings, loaded from .env
    logging_config.py        logging setup

  services/
    transcriber.py            Transcriber interface + WhisperTranscriber
    summarizer.py              Summarizer interface + GeminiSummarizer
    prompts.py                  Gemini prompt template

  pipeline.py                 transcribe() / summarize() - delivery-agnostic
                               core logic

  bot/
    handlers.py                Telegram message handlers
    messages.py                  user-facing text
    transcript_cache.py          per-user transcript cache, used by /retry
    run.py                     builds and starts the bot
```

## Architecture

`Transcriber` and `Summarizer` are abstract interfaces with a single method
each (Strategy pattern). `WhisperTranscriber` and `GeminiSummarizer` are the
current implementations; swapping either provider means adding one class in
`app/services/` and updating `app/bot/run.py`.

`app/pipeline.py` contains the transcribe/summarize logic with no
dependency on Telegram or aiogram. `app/bot/handlers.py` calls into it and
handles only Telegram-specific concerns (message formatting, file download,
file delivery). A future FastAPI adapter could call the same pipeline
functions from an HTTP route without any changes to `app/pipeline.py` or
`app/services/`.

The Gemini prompt (`app/services/prompts.py`) asks for a structured
Markdown summary - Overview, Key Discussion Points, Decisions Made, Action
Items, Next Steps - with inline `**bold**`/`*italic*` spans for labels like
"Responsible:" / "Deadline:". It's generated in whatever language
`WHISPER_LANGUAGE` is set to, via a code-to-name lookup (`LANGUAGE_NAMES`)
so Gemini gets an unambiguous instruction like "Russian" rather than the
raw code `ru`.

`docx_export` and `txt_export` each convert one of those results into a
file: real headings, bullet lists, and bold/italic formatting instead of
literal asterisks for the summary; a plain UTF-8 file for the transcript.
Both live under `app/exporters/` - grouped there for discoverability, and
kept as separate subpackages rather than merged into one module, so
importing `txt_export` never requires `python-docx` to be installed.
Neither imports from `app.bot` (the only Telegram-specific part of the
project), so both work independently of the bot, the same way
`app/pipeline.py` and `app/services/` do:

```bash
python -m app.exporters.docx_export input.md output.docx
python -m app.exporters.txt_export input.txt output.txt
```

```python
from app.exporters.docx_export import render_markdown_summary_to_docx
from app.exporters.txt_export import render_transcript_to_txt
```

Inside this project, `app/bot/handlers.py` calls both functions once per
request, sending the transcript and summary as files by default.

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env   # fill in TOKEN and GEMINI_API_KEY
python main.py
```

## Configuration

All settings are read from environment variables (see `.env.example`):

| Variable                     | Default             | Description                             |
|-------------------------------|----------------------|-------------------------------------------|
| `TOKEN`                       | -                    | Telegram bot token                        |
| `GEMINI_API_KEY`              | -                    | Gemini API key                            |
| `WHISPER_MODEL_SIZE`          | `large-v3-turbo`     | faster-whisper model size                 |
| `WHISPER_LANGUAGE`            | `ru`                 | Language for transcription and summary    |
| `GEMINI_MODEL`                | `gemini-3.1-flash-lite` | Gemini model used for summarization    |
| `GEMINI_MAX_ATTEMPTS`         | `3`                  | Retry attempts on transient errors        |
| `GEMINI_RETRY_DELAY_SECONDS`  | `5`                  | Base delay between retries                |
| `DOWNLOADS_DIR`               | `downloads`          | Local directory for downloaded audio      |

