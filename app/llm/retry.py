import asyncio
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import TypeVar


T = TypeVar("T")


class CircuitOpenError(RuntimeError):
    pass


@dataclass
class CircuitBreaker:
    failure_threshold: int = 3
    recovery_seconds: float = 30.0
    _failures: int = 0
    _opened_at: float | None = None

    def before_call(self) -> None:
        if self._opened_at is None:
            return
        if time.monotonic() - self._opened_at >= self.recovery_seconds:
            self._opened_at = None
            self._failures = 0
            return
        raise CircuitOpenError("LLM circuit breaker is open")

    def record_success(self) -> None:
        self._failures = 0
        self._opened_at = None

    def record_failure(self) -> None:
        self._failures += 1
        if self._failures >= self.failure_threshold:
            self._opened_at = time.monotonic()


async def retry_async(
    operation: Callable[[], Awaitable[T]],
    *,
    attempts: int = 3,
    initial_delay: float = 0.2,
    max_delay: float = 2.0,
    retry_exceptions: tuple[type[BaseException], ...] = (Exception,),
) -> T:
    delay = initial_delay
    last_error: BaseException | None = None
    for attempt in range(attempts):
        try:
            return await operation()
        except retry_exceptions as exc:
            last_error = exc
            if attempt == attempts - 1:
                break
            await asyncio.sleep(delay)
            delay = min(max_delay, delay * 2)
    if last_error is None:
        raise RuntimeError("retry_async failed without an exception")
    raise last_error

