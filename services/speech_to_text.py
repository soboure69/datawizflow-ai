from __future__ import annotations

import importlib.util
import multiprocessing
import os
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any


_MODELS: dict[str, Any] = {}


class WhisperService:
    """Transcription locale. Si PyTorch ne se charge pas dans Streamlit, un processus séparé prend le relais."""

    def __init__(self, model_name: str | None = None) -> None:
        self._model_name = model_name or os.environ.get("WHISPER_MODEL", "small")

    def transcribe(self, audio_bytes: bytes, suffix: str, language: str = "FR") -> str:
        if not audio_bytes:
            raise ValueError("Fichier audio vide.")
        _require_runtime()
        lang = "fr" if (language or "FR").upper() == "FR" else "en"
        extension = suffix if str(suffix).startswith(".") else f".{suffix or 'wav'}"
        try:
            return _transcribe_in_process(self._model_name, audio_bytes, extension, lang)
        except OSError:
            return _transcribe_in_subprocess(self._model_name, audio_bytes, extension, lang)


def whisper_status() -> tuple[bool, str]:
    if not _whisper_installed():
        return False, "openai-whisper non installé"
    if shutil.which("ffmpeg") is None:
        return False, "ffmpeg introuvable"
    return True, "disponible"


def _require_runtime() -> None:
    if not _whisper_installed():
        raise RuntimeError("Whisper n'est pas installé. Lancez : pip install openai-whisper")
    if shutil.which("ffmpeg") is None:
        raise RuntimeError("ffmpeg est introuvable. Installez-le, puis rouvrez le terminal.")


def _whisper_installed() -> bool:
    if "whisper" in sys.modules:
        return True
    return importlib.util.find_spec("whisper") is not None


def _import_whisper() -> Any:
    os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
    import whisper

    return whisper


def _load_model(name: str) -> Any:
    whisper = _import_whisper()
    model = _MODELS.get(name)
    if model is None:
        model = whisper.load_model(name)
        _MODELS[name] = model
    return model


def _transcribe_in_process(model_name: str, audio_bytes: bytes, extension: str, language: str) -> str:
    model = _load_model(model_name)
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / f"question{extension}"
        path.write_bytes(audio_bytes)
        result = model.transcribe(str(path), language=language)
    return _text_or_raise(result)


def _transcribe_in_subprocess(model_name: str, audio_bytes: bytes, extension: str, language: str) -> str:
    ctx = multiprocessing.get_context("spawn")
    queue: multiprocessing.Queue = ctx.Queue()
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / f"question{extension}"
        path.write_bytes(audio_bytes)
        process = ctx.Process(
            target=_whisper_process_entry,
            args=(str(path), model_name, language, queue),
        )
        process.start()
        process.join(600)
        if process.is_alive():
            process.terminate()
            process.join(5)
            raise RuntimeError("La transcription a dépassé 10 minutes.")
        payload = queue.get() if not queue.empty() else None
    if not isinstance(payload, dict) or not payload.get("ok"):
        detail = payload.get("error") if isinstance(payload, dict) else "aucun retour"
        raise RuntimeError(f"La transcription a échoué. {detail}")
    text = str(payload.get("text") or "").strip()
    if not text:
        raise RuntimeError("La transcription est vide.")
    return text


def _whisper_process_entry(audio_path: str, model_name: str, language: str, queue: multiprocessing.Queue) -> None:
    try:
        os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
        import whisper

        model = whisper.load_model(model_name)
        result = model.transcribe(audio_path, language=language)
        queue.put({"ok": True, "text": str(result.get("text") or "").strip()})
    except Exception as exc:
        queue.put({"ok": False, "error": str(exc)})


def _text_or_raise(result: dict[str, Any]) -> str:
    text = str(result.get("text") or "").strip()
    if not text:
        raise RuntimeError("La transcription est vide.")
    return text
