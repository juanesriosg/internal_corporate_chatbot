from __future__ import annotations

from collections import Counter

from app.backend.config import Settings
from app.backend.rag.auth import MockUser, can_access
from app.backend.rag.chunking import tokenize
from app.backend.rag.embeddings import EmbeddingProvider
from app.backend.rag.models import Chunk, RetrievedChunk
from app.backend.rag.storage import load_chunks
from app.backend.rag.vector_store import ChromaVectorStore


class Retriever:
    def __init__(
        self,
        settings: Settings,
        embedding_provider: EmbeddingProvider,
        vector_store: ChromaVectorStore | None = None,
    ) -> None:
        self.settings = settings
        self.embedding_provider = embedding_provider
        self.vector_store = vector_store or ChromaVectorStore.from_settings(settings)
        chunks = load_chunks(settings.local_artifact_dir)
        self.chunk_lookup = {chunk.chunk_id: chunk for chunk in chunks}

    def retrieve(
        self,
        question: str,
        user: MockUser,
        top_k: int | None = None,
    ) -> list[RetrievedChunk]:
        query_embedding = self.embedding_provider.embed_texts([question])[0]
        raw_candidates = self.vector_store.query(
            query_embedding=query_embedding,
            chunk_lookup=self.chunk_lookup,
            candidate_count=max(self.settings.retrieval_candidate_count, (top_k or 5) * 8),
        )
        authorized = [
            candidate for candidate in raw_candidates if can_access(user, candidate.chunk)
        ]
        scored = [self._rescore(question, candidate) for candidate in authorized]
        scored.sort(key=lambda candidate: candidate.score, reverse=True)
        return scored[: top_k or self.settings.retrieval_top_k]

    def _rescore(self, question: str, candidate: RetrievedChunk) -> RetrievedChunk:
        lexical_score = _lexical_score(question, candidate.chunk)
        stale_penalty = (
            0.12 if candidate.chunk.stale and not _query_mentions_stale(question) else 0.0
        )
        score = candidate.vector_score + (0.35 * lexical_score) - stale_penalty
        return RetrievedChunk(
            chunk=candidate.chunk,
            score=score,
            vector_score=candidate.vector_score,
            lexical_score=lexical_score,
        )


def _lexical_score(question: str, chunk: Chunk) -> float:
    query_terms = Counter(_content_tokens(question))
    if not query_terms:
        return 0.0
    chunk_terms = Counter(_content_tokens(f"{chunk.title} {chunk.text}"))
    overlap = sum(min(count, chunk_terms.get(term, 0)) for term, count in query_terms.items())
    title_terms = set(_content_tokens(chunk.title))
    title_overlap = len(set(query_terms).intersection(title_terms))
    return min(1.0, (overlap / max(len(query_terms), 1)) + (0.1 * title_overlap))


def _content_tokens(text: str) -> list[str]:
    stopwords = {
        "a",
        "an",
        "and",
        "are",
        "as",
        "be",
        "can",
        "do",
        "does",
        "for",
        "from",
        "how",
        "if",
        "in",
        "is",
        "it",
        "of",
        "on",
        "or",
        "should",
        "the",
        "to",
        "what",
        "when",
        "which",
        "with",
    }
    return [token for token in tokenize(text) if token not in stopwords and len(token) > 1]


def _query_mentions_stale(question: str) -> bool:
    terms = set(_content_tokens(question))
    return bool(terms.intersection({"2023", "legacy", "stale", "conflict", "superseded", "older"}))


def retrieve_keyword_fallback(
    question: str,
    user: MockUser,
    chunks: list[Chunk],
    top_k: int,
) -> list[RetrievedChunk]:
    authorized = [chunk for chunk in chunks if can_access(user, chunk)]
    candidates: list[RetrievedChunk] = []
    for chunk in authorized:
        lexical_score = _lexical_score(question, chunk)
        if lexical_score <= 0:
            continue
        stale_penalty = 0.12 if chunk.stale and not _query_mentions_stale(question) else 0.0
        score = lexical_score - stale_penalty
        candidates.append(
            RetrievedChunk(
                chunk=chunk,
                score=score,
                vector_score=0.0,
                lexical_score=lexical_score,
            )
        )
    candidates.sort(key=lambda candidate: candidate.score, reverse=True)
    return candidates[:top_k]
