import sys

import pytest

import services.speech_to_text as speech


class _FakeModel:
    def __init__(self, language: str) -> None:
        self.language = language

    def transcribe(self, path: str, language: str) -> dict[str, str]:
        assert path.endswith(".wav")
        self.language = language
        if language == "fr":
            return {"text": " Quel est le chiffre d'affaires par région "}
        return {"text": " Total revenue by region "}


class _FakeWhisper:
    last_model = ""

    @staticmethod
    def load_model(name: str) -> _FakeModel:
        _FakeWhisper.last_model = name
        return _FakeModel("")


@pytest.fixture(autouse=True)
def _whisper_runtime(monkeypatch: pytest.MonkeyPatch) -> None:
    speech._MODELS.clear()
    monkeypatch.setitem(sys.modules, "whisper", _FakeWhisper)
    monkeypatch.setattr(speech.shutil, "which", lambda name: "ffmpeg" if name == "ffmpeg" else None)


def test_transcribe_french() -> None:
    text = speech.WhisperService(model_name="small").transcribe(b"RIFFfake", ".wav", "FR")
    assert text == "Quel est le chiffre d'affaires par région"
    assert _FakeWhisper.last_model == "small"


def test_transcribe_english() -> None:
    text = speech.WhisperService(model_name="small").transcribe(b"RIFFfake", "wav", "EN")
    assert text == "Total revenue by region"


def test_transcribe_reuses_loaded_model(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = {"n": 0}
    original = _FakeWhisper.load_model

    def _counting(name: str) -> _FakeModel:
        calls["n"] += 1
        return original(name)

    monkeypatch.setattr(_FakeWhisper, "load_model", staticmethod(_counting))
    service = speech.WhisperService(model_name="tiny")
    service.transcribe(b"audio", ".wav", "FR")
    service.transcribe(b"audio", ".wav", "EN")
    assert calls["n"] == 1


def test_transcribe_requires_ffmpeg(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(speech.shutil, "which", lambda name: None)
    with pytest.raises(RuntimeError, match="ffmpeg"):
        speech.WhisperService().transcribe(b"audio", ".wav", "FR")
