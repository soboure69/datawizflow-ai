from __future__ import annotations

import os
import subprocess
import tempfile
from pathlib import Path

import pandas as pd


_SCRIPT = r"""
Add-Type -AssemblyName System.Speech
$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
$match = $synth.GetInstalledVoices() | Where-Object { $_.VoiceInfo.Culture.Name -eq $env:TTS_LANG } | Select-Object -First 1
if ($null -ne $match) { $synth.SelectVoice($match.VoiceInfo.Name) }
$text = [System.IO.File]::ReadAllText($env:TTS_TEXT)
$synth.SetOutputToWaveFile($env:TTS_WAV)
$synth.Speak($text)
$synth.Dispose()
"""


def summarize_dataframe(frame: pd.DataFrame, language: str = "FR") -> str:
    """Build a short sentence a voice can read without dumping the whole table."""
    english = (language or "FR").upper() == "EN"
    columns = [str(column) for column in list(frame.columns)[:6]]
    joined = ", ".join(columns) if columns else ("none" if english else "aucune")
    count = len(frame)
    if english:
        row_word = "row" if count == 1 else "rows"
        sentence = f"The query returned {count} {row_word}. Columns: {joined}."
        prefix = " First row: "
        empty = "empty"
    else:
        row_word = "ligne" if count == 1 else "lignes"
        sentence = f"La requête a renvoyé {count} {row_word}. Colonnes : {joined}."
        prefix = " Première ligne : "
        empty = "vide"
    if count and columns:
        row = frame.iloc[0]
        bits = [f"{column} {_speak_value(row[column], empty)}" for column in list(frame.columns)[:4]]
        sentence += prefix + ", ".join(bits) + "."
    return sentence


def synthesize_speech(text: str, language: str = "FR") -> bytes:
    """Return a WAV of the text, spoken by the installed Windows voice."""
    spoken = " ".join(str(text or "").split())
    if not spoken:
        raise ValueError("Rien à lire.")
    if len(spoken) > 600:
        spoken = spoken[:600].rsplit(" ", 1)[0]
    if os.name != "nt":
        raise RuntimeError("La lecture vocale utilise les voix installées sur Windows.")
    culture = "en-US" if (language or "FR").upper() == "EN" else "fr-FR"
    with tempfile.TemporaryDirectory() as tmp:
        folder = Path(tmp)
        script_path = folder / "speak.ps1"
        text_path = folder / "speech.txt"
        wav_path = folder / "speech.wav"
        script_path.write_text(_SCRIPT, encoding="utf-8")
        text_path.write_text(spoken, encoding="utf-8")
        completed = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-File", str(script_path)],
            env={**os.environ, "TTS_TEXT": str(text_path), "TTS_WAV": str(wav_path), "TTS_LANG": culture},
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
        if completed.returncode != 0 or not wav_path.exists() or wav_path.stat().st_size < 44:
            detail = (completed.stderr or completed.stdout or "wav absent").strip()
            raise RuntimeError(f"La lecture vocale a échoué. {detail[:300]}")
        return wav_path.read_bytes()


def _speak_value(value: object, empty: str) -> str:
    if value is None or pd.isna(value):
        return empty
    if isinstance(value, float):
        return f"{value:.2f}".rstrip("0").rstrip(".")
    return str(value)
