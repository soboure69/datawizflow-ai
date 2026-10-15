import subprocess
from pathlib import Path

import pandas as pd
import pytest

import services.text_to_speech as tts


def test_summarize_dataframe_french() -> None:
    frame = pd.DataFrame({"region": ["East"], "revenue": [107872.9]})
    text = tts.summarize_dataframe(frame, "FR")
    assert text.startswith("La requête a renvoyé 1 ligne.")
    assert "region East" in text
    assert "revenue 107872.9" in text


def test_summarize_dataframe_english() -> None:
    frame = pd.DataFrame({"region": ["East"]})
    text = tts.summarize_dataframe(frame, "EN")
    assert text.startswith("The query returned 1 row.")
    assert "First row: region East." in text


def test_synthesize_speech_writes_wav(monkeypatch: pytest.MonkeyPatch) -> None:
    def _fake_run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        env = kwargs["env"]
        assert isinstance(env, dict)
        assert "chiffre" not in " ".join(command)
        Path(str(env["TTS_WAV"])).write_bytes(b"RIFF" + b"\x00" * 40)
        assert Path(str(env["TTS_TEXT"])).read_text(encoding="utf-8") == "Bonjour"
        assert env["TTS_LANG"] == "fr-FR"
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(tts.subprocess, "run", _fake_run)
    monkeypatch.setattr(tts.os, "name", "nt")
    wav = tts.synthesize_speech("Bonjour", "FR")
    assert wav.startswith(b"RIFF")


def test_synthesize_speech_rejects_empty() -> None:
    with pytest.raises(ValueError, match="Rien à lire"):
        tts.synthesize_speech("   ", "FR")
