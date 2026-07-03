from __future__ import annotations

from fastapi.testclient import TestClient


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
    assert payload["refusal"] is False
    assert payload["citations"]
    assert any(citation["title"] == "HR PTO Policy 2026" for citation in payload["citations"])


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
