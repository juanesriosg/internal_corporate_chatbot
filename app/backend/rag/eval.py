from __future__ import annotations

import argparse
import time
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
    eval_start = time.perf_counter()
    settings = settings or Settings(mock_data_dir=source_dir, local_artifact_dir=artifact_dir)
    manifest = load_manifest(source_dir)
    retriever = Retriever(settings, get_embedding_provider(settings))
    eval_user = get_user("eval_user")

    question_results = []
    question_retrieval_ms: list[float] = []
    hits = 0
    for sample in manifest.sample_questions:
        retrieval_start = time.perf_counter()
        retrieved = retriever.retrieve(sample.question, eval_user, top_k=5)
        retrieval_ms = _elapsed_ms(retrieval_start)
        question_retrieval_ms.append(retrieval_ms)
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
                "retrieval_ms": retrieval_ms,
            }
        )

    acl_results = []
    acl_retrieval_ms: list[float] = []
    unauthorized_failures = 0
    for acl_test in manifest.recommended_acl_tests:
        user = get_user(acl_test.user)
        for blocked_title in acl_test.should_not_retrieve:
            retrieval_start = time.perf_counter()
            retrieved = retriever.retrieve(blocked_title, user, top_k=5)
            retrieval_ms = _elapsed_ms(retrieval_start)
            acl_retrieval_ms.append(retrieval_ms)
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
                    "retrieval_ms": retrieval_ms,
                }
            )

    payload = {
        "sample_questions": len(manifest.sample_questions),
        "retrieval_recall_at_5": hits / max(len(manifest.sample_questions), 1),
        "unauthorized_retrieval_failures": unauthorized_failures,
        "latency_ms": {
            "total_eval_ms": _elapsed_ms(eval_start),
            "avg_sample_retrieval_ms": _average(question_retrieval_ms),
            "avg_acl_retrieval_ms": _average(acl_retrieval_ms),
            "max_sample_retrieval_ms": max(question_retrieval_ms, default=0.0),
            "max_acl_retrieval_ms": max(acl_retrieval_ms, default=0.0),
        },
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
    latency = result["latency_ms"]
    print(f"avg_sample_retrieval_ms={latency['avg_sample_retrieval_ms']:.2f}")


def _elapsed_ms(start: float) -> float:
    return round((time.perf_counter() - start) * 1000, 2)


def _average(values: list[float]) -> float:
    if not values:
        return 0.0
    return round(sum(values) / len(values), 2)


if __name__ == "__main__":
    main()
