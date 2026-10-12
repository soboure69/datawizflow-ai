from __future__ import annotations

import json
import os
import re
import urllib.request
from dataclasses import dataclass
from typing import Optional

from ollama import Client

from utils.dataviz_prompts import build_dataviz_prompt
from utils.logger import get_logger
from utils.nl2sql_prompts import build_nl2sql_prompt
from utils.rate_limit import ollama_limiter


_FENCE_RE = re.compile(r"```(?:sql|python)?\s*([\s\S]*?)\s*```", re.IGNORECASE)
_LOGGER = get_logger("ollama")


def _strip_code_fences(text: str) -> str:
    m = _FENCE_RE.search(text)
    if m:
        return m.group(1).strip()
    return text.strip()


@dataclass(frozen=True)
class OllamaSettings:
    base_url: str
    model: str
    temperature: float
    timeout: float


class OllamaService:
    def __init__(
        self,
        *,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        database_url: Optional[str] = None,
        temperature: Optional[float] = None,
        timeout: Optional[float] = None,
    ) -> None:
        self._base_url = base_url or os.environ.get("OLLAMA_URL", "http://localhost:11434")
        self._model = model or os.environ.get("OLLAMA_MODEL", "mistral")
        self._database_url = database_url
        self._temperature = float(temperature if temperature is not None else os.environ.get("OLLAMA_TEMPERATURE", 0.3))
        self._timeout = float(timeout if timeout is not None else os.environ.get("OLLAMA_TIMEOUT", 60))
        self._client = Client(base_url=self._base_url)

    @property
    def settings(self) -> OllamaSettings:
        return OllamaSettings(
            base_url=self._base_url,
            model=self._model,
            temperature=self._temperature,
            timeout=self._timeout,
        )

    def ping(self) -> bool:
        try:
            with urllib.request.urlopen(f"{self._base_url.rstrip('/')}/api/tags", timeout=2) as response:
                return response.status == 200
        except Exception:
            return False

    def list_models(self) -> list[str]:
        with urllib.request.urlopen(f"{self._base_url.rstrip('/')}/api/tags", timeout=3) as response:
            payload = json.loads(response.read().decode("utf-8"))
        return [str(item.get("name")) for item in payload.get("models") or [] if item.get("name")]

    def build_prompt(self, *, question: str, schema: str, language: str, dialect: str = "SQLite") -> str:
        return build_nl2sql_prompt(question=question, schema=schema, language=language, dialect=dialect)

    def generate_sql(
        self,
        *,
        question: str,
        language: str = "FR",
        schema: Optional[str] = None,
        dialect: Optional[str] = None,
    ) -> str:
        if not question or not question.strip():
            raise ValueError("question is required")

        schema_text = schema
        dialect_name = dialect or "SQLite"
        if schema_text is None:
            if not self._database_url:
                raise ValueError("schema is None and database_url was not provided")
            from services.schema_service import describe_schema, dialect_label

            schema_text = describe_schema(self._database_url)
            dialect_name = dialect or dialect_label(self._database_url)

        prompt = self.build_prompt(
            question=question.strip(),
            schema=schema_text,
            language=language,
            dialect=dialect_name,
        )
        sql = _strip_code_fences(self._complete("You output only SQL.", prompt))
        _LOGGER.info("generate_sql model=%s dialect=%s", self._model, dialect_name)
        return sql.strip()

    def generate_viz_spec(
        self,
        *,
        request: str,
        columns: list[str],
        column_types: dict[str, str],
        sample: str,
        library: str,
        language: str = "FR",
    ) -> str:
        if not request or not request.strip():
            raise ValueError("request is required")
        prompt = build_dataviz_prompt(
            request=request.strip(),
            columns=columns,
            column_types=column_types,
            sample=sample,
            library=library,
            language=language,
        )
        spec = _strip_code_fences(self._complete("You output only valid JSON.", prompt))
        _LOGGER.info("generate_viz_spec model=%s library=%s", self._model, library)
        return spec.strip()

    def ask(self, *, system_prompt: str, user_prompt: str) -> str:
        if not user_prompt or not user_prompt.strip():
            raise ValueError("user_prompt is required")
        text = self._complete(system_prompt, user_prompt.strip())
        _LOGGER.info("ask model=%s", self._model)
        return text.strip()

    def _complete(self, system_prompt: str, user_prompt: str) -> str:
        ollama_limiter.check()
        resp = self._client.chat(
            model=self._model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            options={"temperature": self._temperature},
        )
        return str(resp["message"]["content"])
