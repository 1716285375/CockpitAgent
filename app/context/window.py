from app.llm.token_counter import count_tokens


def trim_messages(messages: list[dict], max_tokens: int, keep_recent: int) -> list[dict]:
    if sum(count_tokens(str(m.get("content", ""))) for m in messages) <= max_tokens:
        return messages

    if len(messages) <= keep_recent:
        return messages

    return messages[-keep_recent:]

