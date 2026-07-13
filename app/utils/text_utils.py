def chunk_text(text: str, max_size: int = 4000):
    """Split text into pieces of at most max_size characters, e.g. to fit
    Telegram's message-length limit.
    """
    for i in range(0, len(text), max_size):
        yield text[i : i + max_size]
