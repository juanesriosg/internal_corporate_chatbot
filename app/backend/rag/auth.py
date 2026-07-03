from __future__ import annotations

from dataclasses import dataclass

from app.backend.rag.models import Chunk

DEFAULT_TENANT_ID = "default"


@dataclass(frozen=True)
class MockUser:
    user_id: str
    tenant_id: str
    department: str
    groups: frozenset[str]


MOCK_USERS: dict[str, MockUser] = {
    "all_employee": MockUser(
        user_id="all_employee",
        tenant_id=DEFAULT_TENANT_ID,
        department="HR",
        groups=frozenset({"all-employees"}),
    ),
    "eng_user": MockUser(
        user_id="eng_user",
        tenant_id=DEFAULT_TENANT_ID,
        department="Engineering",
        groups=frozenset({"engineering"}),
    ),
    "finance_user": MockUser(
        user_id="finance_user",
        tenant_id=DEFAULT_TENANT_ID,
        department="Finance",
        groups=frozenset({"finance"}),
    ),
    "security_user": MockUser(
        user_id="security_user",
        tenant_id=DEFAULT_TENANT_ID,
        department="Security",
        groups=frozenset({"security"}),
    ),
    "legal_user": MockUser(
        user_id="legal_user",
        tenant_id=DEFAULT_TENANT_ID,
        department="Legal",
        groups=frozenset({"legal"}),
    ),
    "product_user": MockUser(
        user_id="product_user",
        tenant_id=DEFAULT_TENANT_ID,
        department="Product",
        groups=frozenset({"product"}),
    ),
    "platform_user": MockUser(
        user_id="platform_user",
        tenant_id=DEFAULT_TENANT_ID,
        department="Engineering",
        groups=frozenset({"platform"}),
    ),
    "exec_user": MockUser(
        user_id="exec_user",
        tenant_id=DEFAULT_TENANT_ID,
        department="Executive",
        groups=frozenset({"executives"}),
    ),
    "eval_user": MockUser(
        user_id="eval_user",
        tenant_id=DEFAULT_TENANT_ID,
        department="Evaluation",
        groups=frozenset(
            {
                "ai-platform",
                "all-employees",
                "customer-success",
                "design",
                "engineering",
                "executive-assistants",
                "executives",
                "finance",
                "finance-leads",
                "hr",
                "identity-team",
                "legal",
                "marketing",
                "people-managers",
                "platform",
                "platform-leads",
                "product",
                "security",
                "sre",
                "support",
                "support-leads",
            }
        ),
    ),
}


def get_user(user_id: str) -> MockUser:
    try:
        return MOCK_USERS[user_id]
    except KeyError as exc:
        known = ", ".join(sorted(MOCK_USERS))
        raise KeyError(f"Unknown user_id '{user_id}'. Known mock users: {known}") from exc


def can_access(user: MockUser, chunk: Chunk) -> bool:
    if user.tenant_id != chunk.tenant_id:
        return False
    return bool(user.groups.intersection(chunk.allowed_groups))
