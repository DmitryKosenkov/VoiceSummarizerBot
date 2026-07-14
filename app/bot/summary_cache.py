"""In-memory cache of each user's most recent summary, so /docx can export
it as a Word document without re-generating it via Gemini.
"""

_last_summary: dict[int, str] = {}


def store(user_id: int, summary: str) -> None:
    _last_summary[user_id] = summary


def get(user_id: int) -> str | None:
    return _last_summary.get(user_id)


def clear(user_id: int) -> None:
    _last_summary.pop(user_id, None)
