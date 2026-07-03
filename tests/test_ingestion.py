from __future__ import annotations

from app.backend.config import Settings
from app.backend.rag.ingest import ingest_corpus
from app.backend.rag.manifest import load_manifest, resolve_document_path
from app.backend.rag.parsers import parse_document
from app.backend.rag.storage import load_chunks
from app.backend.rag.vector_store import ChromaVectorStore


def test_manifest_loads_all_documents() -> None:
    manifest = load_manifest(Settings().mock_data_dir)

    assert manifest.document_count == 20
    assert len(manifest.documents) == 20
    assert {document.format for document in manifest.documents} == {
        "docx",
        "html",
        "markdown",
        "pdf",
        "txt",
    }


def test_parser_extracts_each_supported_format(local_settings: Settings) -> None:
    manifest = load_manifest(local_settings.mock_data_dir)
    seen_formats: set[str] = set()

    for document in manifest.documents:
        if document.format in seen_formats:
            continue
        text = parse_document(
            resolve_document_path(local_settings.mock_data_dir, document),
            document,
        )
        assert len(text) > 50
        seen_formats.add(document.format)

    assert seen_formats == {"docx", "html", "markdown", "pdf", "txt"}


def test_ingest_writes_chunks_and_chroma_vectors(local_settings: Settings) -> None:
    summary = ingest_corpus(
        local_settings.mock_data_dir,
        local_settings.local_artifact_dir,
        local_settings,
    )

    chunks = load_chunks(local_settings.local_artifact_dir)
    vector_store = ChromaVectorStore.from_settings(local_settings)

    assert summary["documents"] == 20
    assert summary["chunks"] == len(chunks)
    assert summary["vectors"] == vector_store.count()
    assert len(chunks) >= 20
    assert all(chunk.allowed_groups for chunk in chunks)
