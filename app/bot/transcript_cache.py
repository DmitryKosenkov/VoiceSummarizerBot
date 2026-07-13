"""In-memory cache of each user's most recent transcript, so a failed
summary can be retried via /retry without re-uploading and re-transcribing
the audio.
"""

_last_transcript: dict[int, str] = {}


def store(user_id: int, transcript: str) -> None:
    _last_transcript[user_id] = transcript


def get(user_id: int) -> str | None:
    return _last_transcript.get(user_id)


def clear(user_id: int) -> None:
    _last_transcript.pop(user_id, None)
