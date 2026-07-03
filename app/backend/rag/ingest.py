from __future__ import annotations

import argparse
from pathlib import Path

from app.backend.config import Settings
from app.backend.rag.chunking import chunk_document
from app.backend.rag.embeddings import get_embedding_provider
from app.backend.rag.manifest import load_manifest, resolve_document_path
from app.backend.rag.models import Chunk
from app.backend.rag.parsers import parse_document
from app.backend.rag.storage import write_chunks, write_json
from app.backend.rag.vector_store import ChromaVectorStore


def ingest_corpus(
    source_dir: Path,
    artifact_dir: Path,
    settings: Settings | None = None,
) -> dict[str, int]:
    settings = settings or Settings(mock_data_dir=source_dir, local_artifact_dir=artifact_dir)
    manifest = load_manifest(source_dir)
    chunks: list[Chunk] = []

    for document in manifest.documents:
        path = resolve_document_path(source_dir, document)
        text = parse_document(path, document)
        chunks.extend(
            chunk_document(
                document=document,
                text=text,
                source_dir=source_dir,
                tenant_id=settings.tenant_id,
                max_words=settings.chunk_max_words,
                overlap_words=settings.chunk_overlap_words,
            )
        )

    embedding_provider = get_embedding_provider(settings)
    embeddings = embedding_provider.embed_texts([chunk.text for chunk in chunks])

    artifact_dir.mkdir(parents=True, exist_ok=True)
    write_chunks(artifact_dir, chunks)
    vector_store = ChromaVectorStore(artifact_dir, settings.chroma_collection)
    vector_store.reset()
    vector_store.add_chunks(chunks, embeddings)
    summary = {
        "documents": len(manifest.documents),
        "chunks": len(chunks),
        "vectors": vector_store.count(),
    }
    write_json(artifact_dir / "ingest_summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ingest mock documents into the local vector store."
    )
    parser.add_argument("--source", default="mock_data", type=Path)
    parser.add_argument("--out", default=".local", type=Path)
    args = parser.parse_args()

    settings = Settings(mock_data_dir=args.source, local_artifact_dir=args.out)
    summary = ingest_corpus(args.source, args.out, settings)
    print(
        "Ingested "
        f"{summary['documents']} documents into {summary['chunks']} chunks "
        f"and {summary['vectors']} Chroma vectors."
    )


if __name__ == "__main__":
    main()
