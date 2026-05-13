import asyncio

import pytest

from app.llm.retry import CircuitBreaker, CircuitOpenError, retry_async


def test_retry_async_retries_until_success():
    calls = 0

    async def flaky():
        nonlocal calls
        calls += 1
        if calls < 2:
            raise TimeoutError("temporary")
        return "ok"

    result = asyncio.run(retry_async(flaky, attempts=3, initial_delay=0))

    assert result == "ok"
    assert calls == 2


def test_retry_async_raises_last_error():
    async def failing():
        raise TimeoutError("temporary")

    with pytest.raises(TimeoutError):
        asyncio.run(retry_async(failing, attempts=2, initial_delay=0))


def test_circuit_breaker_opens_after_failures():
    breaker = CircuitBreaker(failure_threshold=2, recovery_seconds=30)

    breaker.record_failure()
    breaker.before_call()
    breaker.record_failure()

    with pytest.raises(CircuitOpenError):
        breaker.before_call()


def test_circuit_breaker_resets_on_success():
    breaker = CircuitBreaker(failure_threshold=2, recovery_seconds=30)

    breaker.record_failure()
    breaker.record_success()
    breaker.before_call()

    assert breaker._failures == 0
