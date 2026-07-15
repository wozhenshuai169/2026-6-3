from collections import defaultdict, deque
from threading import Lock
from time import monotonic

from app.core.errors import AppError
from app.core.config import settings

_windows: dict[str, deque[float]] = defaultdict(deque)
_lock = Lock()


def enforce_rate_limit(bucket: str, identity: str, limit: int, window_seconds: int) -> None:
    if not settings.rate_limit_enabled:
        return
    now = monotonic()
    key = f"{bucket}:{identity}"
    with _lock:
        events = _windows[key]
        cutoff = now - window_seconds
        while events and events[0] <= cutoff:
            events.popleft()
        if len(events) >= limit:
            retry_after = max(1, int(window_seconds - (now - events[0])))
            raise AppError(
                429,
                "RATE_LIMITED",
                "Too many requests, please retry later.",
                headers={"Retry-After": str(retry_after)},
            )
        events.append(now)


def reset_rate_limits_for_tests() -> None:
    with _lock:
        _windows.clear()
