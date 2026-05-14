from collections import defaultdict
from threading import Lock


class MetricsRegistry:
    def __init__(self):
        self._counters: defaultdict[tuple[str, tuple[tuple[str, str], ...]], float] = defaultdict(float)
        self._lock = Lock()

    def increment(self, name: str, value: float = 1.0, **labels: str) -> None:
        key = (name, tuple(sorted((str(k), str(v)) for k, v in labels.items())))
        with self._lock:
            self._counters[key] += value

    def render_prometheus(self) -> str:
        lines: list[str] = []
        with self._lock:
            items = sorted(self._counters.items())
        for (name, labels), value in items:
            label_text = _format_labels(dict(labels))
            lines.append(f"{name}{label_text} {value:g}")
        return "\n".join(lines) + "\n"


def _format_labels(labels: dict[str, str]) -> str:
    if not labels:
        return ""
    values = ",".join(f'{key}="{value}"' for key, value in sorted(labels.items()))
    return "{" + values + "}"
