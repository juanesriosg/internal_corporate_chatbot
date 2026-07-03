from __future__ import annotations

import argparse
from pathlib import Path

from app.backend.config import Settings
from app.backend.rag.auth import get_user
from app.backend.rag.embeddings import get_embedding_provider
from app.backend.rag.manifest import load_manifest
from app.backend.rag.retriever import Retriever
from app.backend.rag.storage import write_json


def evaluate(
    source_dir: Path,
    artifact_dir: Path,
    settings: Settings | None = None,
) -> dict[str, object]:
    settings = settings or Settings(mock_data_dir=source_dir, local_artifact_dir=artifact_dir)
    manifest = load_manifest(source_dir)
    retriever = Retriever(settings, get_embedding_provider(settings))
    eval_user = get_user("eval_user")

    question_results = []
    hits = 0
    for sample in manifest.sample_questions:
        retrieved = retriever.retrieve(sample.question, eval_user, top_k=5)
        titles = [candidate.chunk.title for candidate in retrieved]
        sources = [Path(candidate.chunk.source_uri).name for candidate in retrieved]
        expected_names = [
            part.strip() for part in sample.expected_source.split("+") if part.strip()
        ]
        searchable = " ".join([*sources, *titles]).lower()
        hit = all(expected.lower() in searchable for expected in expected_names)
        hits += int(hit)
        question_results.append(
            {
                "question": sample.question,
                "expected_source": sample.expected_source,
                "retrieved_titles": titles,
                "hit_at_5": hit,
            }
        )

    acl_results = []
    unauthorized_failures = 0
    for acl_test in manifest.recommended_acl_tests:
        user = get_user(acl_test.user)
        for blocked_title in acl_test.should_not_retrieve:
            retrieved = retriever.retrieve(blocked_title, user, top_k=5)
            titles = [candidate.chunk.title for candidate in retrieved]
            leaked = blocked_title in titles
            unauthorized_failures += int(leaked)
            acl_results.append(
                {
                    "user": acl_test.user,
                    "query": blocked_title,
                    "blocked_title": blocked_title,
                    "retrieved_titles": titles,
                    "passed": not leaked,
                }
            )

    payload = {
        "sample_questions": len(manifest.sample_questions),
        "retrieval_recall_at_5": hits / max(len(manifest.sample_questions), 1),
        "unauthorized_retrieval_failures": unauthorized_failures,
        "question_results": question_results,
        "acl_results": acl_results,
    }
    write_json(artifact_dir / "eval_results.json", payload)
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate retrieval and ACL behavior.")
    parser.add_argument("--source", default="mock_data", type=Path)
    parser.add_argument("--index", default=".local", type=Path)
    args = parser.parse_args()

    settings = Settings(mock_data_dir=args.source, local_artifact_dir=args.index)
    result = evaluate(args.source, args.index, settings)
    print(f"retrieval_recall_at_5={result['retrieval_recall_at_5']:.2f}")
    print(f"unauthorized_retrieval_failures={result['unauthorized_retrieval_failures']}")


if __name__ == "__main__":
    main()
