from app.llm.token_counter import count_tokens


class SimpleCompressor:
    async def compress(self, messages: list[dict], target_tokens: int = 220) -> str:
        fragments: list[str] = []
        for message in messages:
            role = message.get("role", "unknown")
            content = str(message.get("content", "")).replace("\n", " ").strip()
            if content:
                fragments.append(f"{role}: {content}")

        summary = " | ".join(fragments)
        while count_tokens(summary) > target_tokens and len(summary) > 80:
            summary = summary[: int(len(summary) * 0.75)].rstrip()
        return summary or "无历史摘要"

