from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path

from app.backend.rag.models import Chunk

CHUNKS_FILENAME = "chunks.jsonl"
FEEDBACK_FILENAME = "feedback.jsonl"


def chunks_path(artifact_dir: Path) -> Path:
    return artifact_dir / CHUNKS_FILENAME


def write_chunks(artifact_dir: Path, chunks: Iterable[Chunk]) -> None:
    artifact_dir.mkdir(parents=True, exist_ok=True)
    path = chunks_path(artifact_dir)
    with path.open("w", encoding="utf-8") as handle:
        for chunk in chunks:
            handle.write(chunk.to_jsonl())
            handle.write("\n")


def load_chunks(artifact_dir: Path) -> list[Chunk]:
    path = chunks_path(artifact_dir)
    if not path.exists():
        raise FileNotFoundError(f"Chunk file not found: {path}. Run ingestion first.")
    chunks = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                chunks.append(Chunk.model_validate_json(line))
    return chunks


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def append_jsonl(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True))
        handle.write("\n")


def feedback_path(artifact_dir: Path) -> Path:
    return artifact_dir / FEEDBACK_FILENAME
