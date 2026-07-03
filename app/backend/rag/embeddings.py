from __future__ import annotations

import hashlib
import math
from collections.abc import Sequence

from openai import AzureOpenAI, OpenAI

from app.backend.config import LLMProvider, Settings
from app.backend.rag.chunking import tokenize


class EmbeddingProvider:
    def embed_texts(self, texts: Sequence[str]) -> list[list[float]]:
        raise NotImplementedError


class LocalHashEmbeddingProvider(EmbeddingProvider):
    """Small deterministic embedding provider for no-key local tests."""

    def __init__(self, dimensions: int = 384) -> None:
        self.dimensions = dimensions

    def embed_texts(self, texts: Sequence[str]) -> list[list[float]]:
        return [self._embed(text) for text in texts]

    def _embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        tokens = tokenize(text)
        for token in tokens:
            digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
            value = int.from_bytes(digest, "big")
            index = value % self.dimensions
            sign = -1.0 if value & 1 else 1.0
            vector[index] += sign
        norm = math.sqrt(sum(value * value for value in vector))
        if norm == 0:
            return vector
        return [value / norm for value in vector]


class OpenAIEmbeddingProvider(EmbeddingProvider):
    def __init__(self, settings: Settings) -> None:
        settings.require_openai_embeddings()
        self.client = OpenAI(
            api_key=settings.openai_api_key,
            timeout=settings.openai_timeout_seconds,
        )
        self.model = settings.openai_embedding_model

    def embed_texts(self, texts: Sequence[str]) -> list[list[float]]:
        if not texts:
            return []
        response = self.client.embeddings.create(model=self.model, input=list(texts))
        return [item.embedding for item in response.data]


class AzureOpenAIEmbeddingProvider(EmbeddingProvider):
    def __init__(self, settings: Settings) -> None:
        settings.require_azure_openai()
        self.client = AzureOpenAI(
            api_key=settings.azure_openai_api_key,
            azure_endpoint=settings.azure_openai_endpoint,
            api_version=settings.azure_openai_api_version,
            timeout=settings.openai_timeout_seconds,
        )
        self.deployment = settings.azure_openai_embedding_deployment

    def embed_texts(self, texts: Sequence[str]) -> list[list[float]]:
        if not texts:
            return []
        response = self.client.embeddings.create(model=self.deployment, input=list(texts))
        return [item.embedding for item in response.data]


def get_embedding_provider(settings: Settings) -> EmbeddingProvider:
    if settings.llm_provider == LLMProvider.OPENAI:
        return OpenAIEmbeddingProvider(settings)
    if settings.llm_provider == LLMProvider.AZURE_OPENAI:
        return AzureOpenAIEmbeddingProvider(settings)
    return LocalHashEmbeddingProvider(dimensions=settings.local_embedding_dimensions)
