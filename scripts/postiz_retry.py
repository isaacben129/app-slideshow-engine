"""Retry-with-backoff for Postiz publish calls.

A transient network outage (e.g. the host losing data for an hour) must not
zero out a day of scheduled content. Wrap the full async publish in a retry
loop: each attempt re-runs asyncio.run() so it opens a FRESH MCP connection,
which is exactly what we want after a dropped socket.

Only connection/network-style errors are retried. Logical errors (bad payload,
auth failure, validation) propagate immediately so they surface instead of
being masked by silent retries.
"""
from __future__ import annotations

import asyncio
import re
import time

# Connection / network-ish error signatures worth retrying.
_CONN_RE = re.compile(
    r"connection|connect|timeout|timed out|network|reset|refused|"
    r"unreachable|temporary failure|stream|eof|broken pipe|name or service",
    re.I,
)


def _is_retryable(exc: BaseException) -> bool:
    return bool(_CONN_RE.search(f"{type(exc).__name__}: {exc}"))


def retry_publish(coro_factory, *, attempts: int = 6, base_delay: float = 30.0,
                  max_delay: float = 600.0):
    """Run an async publish coroutine with retry/backoff.

    `coro_factory()` must return a FRESH coroutine each call (we call
    asyncio.run() per attempt so every attempt gets a clean MCP connection).
    Raises RuntimeError after exhaustion; the message is prefixed so a cron
    failure report is unmistakable.
    """
    last_exc: BaseException | None = None
    for attempt in range(1, attempts + 1):
        try:
            return asyncio.run(coro_factory())
        except Exception as exc:  # noqa: BLE001 - re-raised intentionally
            last_exc = exc
            if not _is_retryable(exc):
                raise  # logical error -> do not retry
            if attempt == attempts:
                break  # exhausted retries
            delay = min(base_delay * (2 ** (attempt - 1)), max_delay)
            print(
                f"[retry] Postiz publish attempt {attempt} failed "
                f"({type(exc).__name__}: {exc}); retrying in {int(delay)}s "
                f"(attempt {attempt + 1}/{attempts})",
                flush=True,
            )
            time.sleep(delay)
    raise RuntimeError(
        f"[POSTIZ PUBLISH FAILED AFTER {attempts} ATTEMPTS] {last_exc}"
    )
