from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import chromadb
from chromadb.errors import InvalidDimensionException

from app.backend.config import Settings
from app.backend.rag.models import Chunk, RetrievedChunk


def chroma_path(artifact_dir: Path) -> Path:
    return artifact_dir / "vector_index"


class ChromaVectorStore:
    def __init__(self, artifact_dir: Path, collection_name: str) -> None:
        self.artifact_dir = artifact_dir
        self.path = chroma_path(artifact_dir)
        self.collection_name = collection_name
        self.client = chromadb.PersistentClient(path=str(self.path))
        self.collection = self.client.get_or_create_collection(name=collection_name)

    @classmethod
    def from_settings(cls, settings: Settings) -> ChromaVectorStore:
        return cls(settings.local_artifact_dir, settings.chroma_collection)

    def reset(self) -> None:
        self.path.mkdir(parents=True, exist_ok=True)
        try:
            self.client.delete_collection(self.collection_name)
        except Exception:
            pass
        self.collection = self.client.get_or_create_collection(name=self.collection_name)

    def add_chunks(
        self,
        chunks: list[Chunk],
        embeddings: list[list[float]],
        batch_size: int = 100,
    ) -> None:
        if len(chunks) != len(embeddings):
            raise ValueError(f"chunks={len(chunks)} embeddings={len(embeddings)}")

        for start in range(0, len(chunks), batch_size):
            batch_chunks = chunks[start : start + batch_size]
            batch_embeddings = embeddings[start : start + batch_size]
            self.collection.add(
                ids=[chunk.chunk_id for chunk in batch_chunks],
                documents=[chunk.text for chunk in batch_chunks],
                embeddings=batch_embeddings,
                metadatas=[_chunk_metadata(chunk) for chunk in batch_chunks],
            )

    def count(self) -> int:
        return self.collection.count()

    def query(
        self,
        query_embedding: list[float],
        chunk_lookup: dict[str, Chunk],
        candidate_count: int,
    ) -> list[RetrievedChunk]:
        if self.collection.count() == 0:
            return []
        try:
            result = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=min(candidate_count, self.collection.count()),
                include=["distances", "metadatas", "documents"],
            )
        except InvalidDimensionException as exc:
            raise RuntimeError(
                "The existing Chroma index was built with a different embedding "
                "dimension than the current embedding provider. Rebuild it with "
                "`python -m app.backend.rag.ingest --source mock_data --out .local`, "
                "or delete `.local` and ingest again."
            ) from exc
        retrieved: list[RetrievedChunk] = []
        ids = result.get("ids", [[]])[0]
        distances = result.get("distances", [[]])[0]
        for chunk_id, distance in zip(ids, distances, strict=False):
            chunk = chunk_lookup.get(chunk_id)
            if chunk is None:
                continue
            vector_score = 1.0 / (1.0 + float(distance))
            retrieved.append(
                RetrievedChunk(
                    chunk=chunk,
                    score=vector_score,
                    vector_score=vector_score,
                    lexical_score=0.0,
                )
            )
        return retrieved


def index_present(artifact_dir: Path) -> bool:
    return chroma_path(artifact_dir).exists()


def _chunk_metadata(chunk: Chunk) -> dict[str, Any]:
    return {
        "doc_id": chunk.doc_id,
        "title": chunk.title,
        "source_uri": chunk.source_uri,
        "tenant_id": chunk.tenant_id,
        "department": chunk.department,
        "category": chunk.category,
        "sensitivity": chunk.sensitivity,
        "allowed_groups": json.dumps(chunk.allowed_groups),
        "stale": chunk.stale,
        "chunk_index": chunk.chunk_index,
    }
