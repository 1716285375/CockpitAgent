class TokenCounter:
    def __init__(self, model: str = "gpt-4o-mini"):
        self.model = model
        self._encoding = self._load_encoding(model)

    def count(self, text: str) -> int:
        if not text:
            return 0
        if self._encoding is not None:
            return len(self._encoding.encode(text))
        return estimate_tokens(text)

    @staticmethod
    def _load_encoding(model: str):
        try:
            import tiktoken
        except ImportError:
            return None
        try:
            return tiktoken.encoding_for_model(model)
        except KeyError:
            return tiktoken.get_encoding("cl100k_base")


def estimate_tokens(text: str) -> int:
    """Small dependency-free estimate good enough for context trimming."""
    if not text:
        return 0
    ascii_chars = sum(1 for ch in text if ord(ch) < 128)
    cjk_chars = len(text) - ascii_chars
    return max(1, ascii_chars // 4 + cjk_chars)


_default_counter = TokenCounter()


def count_tokens(text: str) -> int:
    return _default_counter.count(text)
