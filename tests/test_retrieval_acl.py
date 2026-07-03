from __future__ import annotations

from app.backend.config import Settings
from app.backend.rag.auth import get_user
from app.backend.rag.embeddings import get_embedding_provider
from app.backend.rag.retriever import Retriever


def test_retrieves_hr_policy_for_all_employee(ingested_settings: Settings) -> None:
    retriever = Retriever(ingested_settings, get_embedding_provider(ingested_settings))
    retrieved = retriever.retrieve(
        "How many PTO days do full-time employees receive?",
        get_user("all_employee"),
        top_k=5,
    )

    titles = [candidate.chunk.title for candidate in retrieved]
    assert "HR PTO Policy 2026" in titles
    assert all("Finance" not in title for title in titles)


def test_acl_blocks_finance_restricted_docs_for_engineering_user(
    ingested_settings: Settings,
) -> None:
    retriever = Retriever(ingested_settings, get_embedding_provider(ingested_settings))
    retrieved = retriever.retrieve(
        "What are the finance quarter close action items?",
        get_user("eng_user"),
        top_k=8,
    )

    titles = [candidate.chunk.title for candidate in retrieved]
    assert "Finance Quarter Close Notes - Confidential" not in titles
    assert "Finance Travel Reimbursement Policy - Confidential" not in titles


def test_finance_user_can_retrieve_finance_docs(ingested_settings: Settings) -> None:
    retriever = Retriever(ingested_settings, get_embedding_provider(ingested_settings))
    retrieved = retriever.retrieve(
        "What are the finance quarter close action items?",
        get_user("finance_user"),
        top_k=5,
    )

    titles = [candidate.chunk.title for candidate in retrieved]
    assert "Finance Quarter Close Notes - Confidential" in titles

