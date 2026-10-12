import services.ollama_service as ollama_service
from services.ollama_service import OllamaService


class _FakeClient:
    def __init__(self, *, base_url: str):
        self.base_url = base_url

    def chat(self, *, model: str, messages, **kwargs):
        return {"message": {"content": "```sql\nSELECT 1 AS ok\n```"}}


def test_generate_sql_strips_code_fences(monkeypatch) -> None:
    monkeypatch.setattr(ollama_service, "Client", _FakeClient)

    svc = OllamaService(base_url="http://localhost:11434", model="mistral", database_url="sqlite:///db/demo.db")
    sql = svc.generate_sql(question="irrelevant", language="EN", schema="TABLE t(a INTEGER)")
    assert sql == "SELECT 1 AS ok"
