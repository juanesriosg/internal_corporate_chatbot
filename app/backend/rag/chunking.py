from __future__ import annotations

import hashlib
import re
from pathlib import Path

from app.backend.rag.models import Chunk, DocumentRecord

TOKEN_RE = re.compile(r"\b[\w'-]+\b")


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.lower()).strip("-")
    return slug or "document"


def stable_doc_id(document: DocumentRecord) -> str:
    digest = hashlib.sha1(document.file.encode("utf-8")).hexdigest()[:8]
    return f"{slugify(document.title)}-{digest}"


def chunk_document(
    document: DocumentRecord,
    text: str,
    source_dir: Path,
    tenant_id: str,
    max_words: int,
    overlap_words: int,
) -> list[Chunk]:
    doc_id = stable_doc_id(document)
    paragraphs = _paragraphs_with_title(document.title, text)
    windows = _paragraph_windows(paragraphs, max_words=max_words, overlap_words=overlap_words)
    chunks: list[Chunk] = []
    for index, window_text in enumerate(windows):
        chunk_id = f"{doc_id}#{index:04d}"
        chunks.append(
            Chunk(
                chunk_id=chunk_id,
                doc_id=doc_id,
                text=window_text,
                title=document.title,
                source_uri=str(source_dir / document.file),
                tenant_id=tenant_id,
                department=document.department,
                category=document.category,
                sensitivity=document.sensitivity,
                allowed_groups=document.allowed_groups,
                stale=document.stale,
                chunk_index=index,
            )
        )
    return chunks


def word_count(text: str) -> int:
    return len(TOKEN_RE.findall(text))


def tokenize(text: str) -> list[str]:
    return [token.lower() for token in TOKEN_RE.findall(text)]


def _paragraphs_with_title(title: str, text: str) -> list[str]:
    paragraphs = [title]
    for raw in re.split(r"\n\s*\n", text):
        paragraph = raw.strip()
        if paragraph:
            paragraphs.append(paragraph)
    return paragraphs


def _paragraph_windows(paragraphs: list[str], max_words: int, overlap_words: int) -> list[str]:
    chunks: list[str] = []
    current: list[str] = []
    current_words = 0

    for paragraph in paragraphs:
        count = word_count(paragraph)
        if current and current_words + count > max_words:
            chunks.append("\n\n".join(current).strip())
            overlap = _tail_words(current, overlap_words)
            current = [overlap] if overlap else []
            current_words = word_count(overlap)
        current.append(paragraph)
        current_words += count

    if current:
        chunks.append("\n\n".join(current).strip())

    if not chunks and paragraphs:
        chunks.append("\n\n".join(paragraphs).strip())

    return chunks


def _tail_words(paragraphs: list[str], overlap_words: int) -> str:
    if overlap_words <= 0:
        return ""
    words = TOKEN_RE.findall("\n\n".join(paragraphs))
    if not words:
        return ""
    return " ".join(words[-overlap_words:])

