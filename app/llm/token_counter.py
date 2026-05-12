def count_tokens(text: str) -> int:
    """Small dependency-free estimate good enough for context trimming."""
    if not text:
        return 0
    ascii_chars = sum(1 for ch in text if ord(ch) < 128)
    cjk_chars = len(text) - ascii_chars
    return max(1, ascii_chars // 4 + cjk_chars)

