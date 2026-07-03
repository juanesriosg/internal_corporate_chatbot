from __future__ import annotations

from types import SimpleNamespace

from app.backend.config import LLMProvider, Settings
from app.backend.rag.generator import OpenAIAnswerGenerator
from app.backend.rag.models import Chunk, RetrievedChunk


class FakeCompletions:
    def __init__(self) -> None:
        self.kwargs = {}

    def create(self, **kwargs):
        self.kwargs = kwargs
        message = SimpleNamespace(content="Answer from context.")
        choice = SimpleNamespace(message=message)
        return SimpleNamespace(choices=[choice])


class FakeClient:
    def __init__(self) -> None:
        self.completions = FakeCompletions()
        self.chat = SimpleNamespace(completions=self.completions)


def test_openai_generator_uses_max_completion_tokens() -> None:
    settings = Settings(
        llm_provider=LLMProvider.OPENAI,
        openai_api_key="test-key",
        openai_chat_model="gpt-5.4-mini",
        openai_max_output_tokens=123,
    )
    client = FakeClient()
    generator = object.__new__(OpenAIAnswerGenerator)
    generator.settings = settings
    generator.client = client

    answer, refusal = generator.generate("What is the policy?", [_retrieved_chunk()])

    assert answer == "Answer from context."
    assert refusal is False
    assert client.completions.kwargs["max_completion_tokens"] == 123
    assert "max_tokens" not in client.completions.kwargs


def _retrieved_chunk() -> RetrievedChunk:
    chunk = Chunk(
        chunk_id="doc#0001",
        doc_id="doc",
        text="The policy says answers must cite authorized context.",
        title="Policy",
        source_uri="mock_data/policy.md",
        tenant_id="default",
        department="Engineering",
        category="Policy",
        sensitivity="internal",
        allowed_groups=["engineering"],
        stale=False,
        chunk_index=0,
    )
    return RetrievedChunk(chunk=chunk, score=1.0, vector_score=1.0, lexical_score=1.0)
