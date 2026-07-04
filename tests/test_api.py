from __future__ import annotations

import json

from fastapi.testclient import TestClient

from app.backend.config import Settings


def test_health_reports_local_index(api_client: TestClient) -> None:
    response = api_client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["index_present"] is True
    assert payload["collection_count"] > 0


def test_chat_returns_grounded_citation(api_client: TestClient) -> None:
    response = api_client.post(
        "/chat",
        json={
            "user_id": "all_employee",
            "question": "How many PTO days do full-time employees receive?",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["request_id"]
    assert payload["refusal"] is False
    assert payload["citations"]
    assert payload["fallback_used"] is False
    assert payload["timings_ms"]["total_ms"] >= 0
    assert any(citation["title"] == "HR PTO Policy 2026" for citation in payload["citations"])
    assert any(source["title"] == "HR PTO Policy 2026" for source in payload["retrieved_sources"])
    assert all("#" not in source["title"] for source in payload["retrieved_sources"])


def test_chat_does_not_leak_unauthorized_finance_doc(api_client: TestClient) -> None:
    response = api_client.post(
        "/chat",
        json={
            "user_id": "eng_user",
            "question": "What are the finance quarter close action items?",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["refusal"] is True
    assert "Finance Quarter Close Notes - Confidential" not in {
        citation["title"] for citation in payload["citations"]
    }
    assert "Finance Travel Reimbursement Policy - Confidential" not in {
        citation["title"] for citation in payload["citations"]
    }


def test_chat_requires_basic_auth_when_enabled(
    api_client: TestClient,
    monkeypatch,
) -> None:
    monkeypatch.setenv("API_AUTH_ENABLED", "true")
    monkeypatch.setenv("API_BASIC_USERNAME", "reviewer")
    monkeypatch.setenv("API_BASIC_PASSWORD", "local-password")

    unauthenticated = api_client.post(
        "/chat",
        json={
            "user_id": "all_employee",
            "question": "How many PTO days do full-time employees receive?",
        },
    )
    assert unauthenticated.status_code == 401

    authenticated = api_client.post(
        "/chat",
        auth=("reviewer", "local-password"),
        json={
            "user_id": "all_employee",
            "question": "How many PTO days do full-time employees receive?",
        },
    )
    assert authenticated.status_code == 200
    assert authenticated.json()["refusal"] is False


def test_chat_falls_back_to_local_when_openai_provider_fails(
    api_client: TestClient,
    monkeypatch,
) -> None:
    def fail_embedding_provider(settings: Settings):
        raise RuntimeError("OpenAI unavailable")

    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_CHAT_MODEL", "gpt-5.4-mini")
    monkeypatch.setattr("app.backend.main.get_embedding_provider", fail_embedding_provider)

    response = api_client.post(
        "/chat",
        json={
            "user_id": "all_employee",
            "question": "How many PTO days do full-time employees receive?",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["fallback_used"] is True
    assert payload["fallback_reason"] == "RuntimeError"
    assert payload["provider"] == "openai->local"
    assert "local fallback answer composer" in payload["answer"]
    assert payload["timings_ms"]["fallback_ms"] >= 0


def test_feedback_writes_local_jsonl(
    api_client: TestClient,
    ingested_settings: Settings,
) -> None:
    response = api_client.post(
        "/feedback",
        json={
            "request_id": "req_test",
            "user_id": "all_employee",
            "rating": "down",
            "question": "What is PTO?",
            "answer": "A test answer.",
            "comment": "Missing detail.",
        },
    )

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "request_id": "req_test"}

    feedback_path = ingested_settings.local_artifact_dir / "feedback.jsonl"
    payload = json.loads(feedback_path.read_text(encoding="utf-8").strip().splitlines()[-1])
    assert payload["request_id"] == "req_test"
    assert payload["rating"] == "down"
    assert payload["comment"] == "Missing detail."
    assert payload["created_at"]

    list_response = api_client.get("/feedback")
    assert list_response.status_code == 200
    list_payload = list_response.json()
    assert list_payload["status"] == "ready"
    assert list_payload["count"] >= 1
    assert list_payload["records"][0]["request_id"] == "req_test"


def test_eval_results_reads_local_artifact(
    api_client: TestClient,
    ingested_settings: Settings,
) -> None:
    expected = {
        "sample_questions": 1,
        "retrieval_recall_at_5": 1.0,
        "unauthorized_retrieval_failures": 0,
        "latency_ms": {"avg_sample_retrieval_ms": 12.3},
        "question_results": [
            {
                "question": "What is PTO?",
                "expected_source": "HR_PTO_Policy_2026.pdf",
                "hit": True,
                "retrieval_ms": 12.3,
                "retrieved_titles": ["HR PTO Policy 2026"],
            }
        ],
        "acl_results": [],
    }
    eval_path = ingested_settings.local_artifact_dir / "eval_results.json"
    eval_path.write_text(json.dumps(expected), encoding="utf-8")

    response = api_client.get("/eval-results")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ready"
    assert payload["artifact"].endswith("eval_results.json")
    assert payload["results"] == expected
