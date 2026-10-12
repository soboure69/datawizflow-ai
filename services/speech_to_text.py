from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path
from typing import Any


_MODELS: dict[str, Any] = {}


class WhisperService:
    """Transcription locale via openai-whisper. Le modèle reste en mémoire après le premier appel."""

    def __init__(self, model_name: str | None = None) -> None:
        self._model_name = model_name or os.environ.get("WHISPER_MODEL", "small")

    def transcribe(self, audio_bytes: bytes, suffix: str, language: str = "FR") -> str:
        if not audio_bytes:
            raise ValueError("Fichier audio vide.")
        _require_runtime()
        lang = "fr" if (language or "FR").upper() == "FR" else "en"
        model = _load_model(self._model_name)
        extension = suffix if str(suffix).startswith(".") else f".{suffix or 'wav'}"
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / f"question{extension}"
            path.write_bytes(audio_bytes)
            result = model.transcribe(str(path), language=lang)
        text = str(result.get("text") or "").strip()
        if not text:
            raise RuntimeError("La transcription est vide.")
        return text


def whisper_status() -> tuple[bool, str]:
    try:
        import whisper  # noqa: F401
    except ImportError:
        return False, "openai-whisper non installé"
    if shutil.which("ffmpeg") is None:
        return False, "ffmpeg introuvable"
    return True, "disponible"


def _require_runtime() -> None:
    try:
        import whisper  # noqa: F401
    except ImportError as exc:
        raise RuntimeError("Whisper n'est pas installé. Lancez : pip install openai-whisper") from exc
    if shutil.which("ffmpeg") is None:
        raise RuntimeError("ffmpeg est introuvable. Installez-le, puis rouvrez le terminal.")


def _load_model(name: str) -> Any:
    import whisper

    model = _MODELS.get(name)
    if model is None:
        model = whisper.load_model(name)
        _MODELS[name] = model
    return model
