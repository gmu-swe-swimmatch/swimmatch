"""Throttle repeated failed logins.

Failures are counted per (client IP, email) inside a sliding window. Once the limit is hit,
that pair is blocked until the oldest failure ages out of the window. Keying on the pair
means someone guessing from another IP can't lock a real user out of their own account.

State lives in memory, which is fine for the single-process dev server. A multi-worker
deployment would need a shared store (e.g. Redis) instead.
"""
import threading
import time
from collections import defaultdict, deque

MAX_FAILURES = 5
WINDOW_SECONDS = 15 * 60

_failures = defaultdict(deque)
_lock = threading.Lock()


def _key(ip, email):
    return (ip or "unknown", (email or "").strip().lower())


def _prune(attempts, now, window):
    while attempts and now - attempts[0] >= window:
        attempts.popleft()


def retry_after(ip, email, max_failures=MAX_FAILURES, window=WINDOW_SECONDS, now=None):
    """Seconds until this ip/email may try again, or 0 if not blocked."""
    now = time.monotonic() if now is None else now
    key = _key(ip, email)
    with _lock:
        attempts = _failures.get(key)
        if not attempts:
            return 0
        _prune(attempts, now, window)
        if len(attempts) < max_failures:
            if not attempts:
                _failures.pop(key, None)
            return 0
        return max(1, int(window - (now - attempts[0])) + 1)


def record_failure(ip, email, now=None):
    now = time.monotonic() if now is None else now
    with _lock:
        _failures[_key(ip, email)].append(now)


def clear(ip, email):
    with _lock:
        _failures.pop(_key(ip, email), None)


def reset_all():
    """Forget every recorded failure (used by tests)."""
    with _lock:
        _failures.clear()
