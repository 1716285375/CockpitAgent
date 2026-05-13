from app.llm.token_counter import TokenCounter, count_tokens, estimate_tokens


def test_estimate_tokens_handles_ascii_and_cjk():
    assert estimate_tokens("hello world") >= 1
    assert estimate_tokens("你好世界") == 4


def test_count_tokens_uses_default_counter():
    assert count_tokens("hello") >= 1


def test_token_counter_falls_back_for_unknown_model():
    counter = TokenCounter("unknown-model")

    assert counter.count("hello") >= 1
