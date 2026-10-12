import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture(autouse=True)
def _disable_ollama_rate_limit() -> None:
    from utils.rate_limit import ollama_limiter

    previous = ollama_limiter._min_interval
    ollama_limiter._min_interval = 0
    yield
    ollama_limiter._min_interval = previous