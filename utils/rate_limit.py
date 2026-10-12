from __future__ import annotations

import threading
import time


class RateLimiter:
    """Limite simple entre deux appels LLM dans le même processus."""

    def __init__(self, min_interval_seconds: float = 1.0) -> None:
        self._min_interval = min_interval_seconds
        self._last = 0.0
        self._lock = threading.Lock()

    def check(self) -> None:
        with self._lock:
            now = time.monotonic()
            elapsed = now - self._last
            if self._last and elapsed < self._min_interval:
                raise RuntimeError("Trop d'appels au modèle. Attendez une seconde puis réessayez.")
            self._last = now


ollama_limiter = RateLimiter(min_interval_seconds=1.0)
