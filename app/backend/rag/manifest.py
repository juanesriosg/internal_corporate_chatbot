from __future__ import annotations

import json
from pathlib import Path

from app.backend.rag.models import DocumentRecord, Manifest


def load_manifest(source_dir: Path) -> Manifest:
    manifest_path = source_dir / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest = Manifest.model_validate(data)
    if manifest.document_count != len(manifest.documents):
        raise ValueError(
            f"Manifest document_count={manifest.document_count} but "
            f"documents={len(manifest.documents)}."
        )
    return manifest


def resolve_document_path(source_dir: Path, document: DocumentRecord) -> Path:
    path = source_dir / document.source_path
    if not path.exists():
        raise FileNotFoundError(f"Document not found for manifest entry {document.title}: {path}")
    return path

