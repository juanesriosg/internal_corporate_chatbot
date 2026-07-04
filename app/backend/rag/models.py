from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field

JsonDict = dict[str, Any]


class DocumentRecord(BaseModel):
    file: str
    title: str
    format: str
    category: str
    department: str
    sensitivity: str
    allowed_groups: list[str] = Field(default_factory=list)
    stale: bool = False
    description: str = ""

    @property
    def source_path(self) -> Path:
        return Path(self.file)


class AclTest(BaseModel):
    user: str
    groups: list[str]
    should_retrieve: list[str]
    should_not_retrieve: list[str]


class SampleQuestion(BaseModel):
    question: str
    expected_source: str


class Manifest(BaseModel):
    corpus_name: str
    created_at: str
    purpose: str
    document_count: int
    formats: list[str]
    documents: list[DocumentRecord]
    recommended_acl_tests: list[AclTest] = Field(default_factory=list)
    sample_questions: list[SampleQuestion] = Field(default_factory=list)


class Chunk(BaseModel):
    chunk_id: str
    doc_id: str
    text: str
    title: str
    source_uri: str
    tenant_id: str
    department: str
    category: str
    sensitivity: str
    allowed_groups: list[str]
    stale: bool
    chunk_index: int

    def to_jsonl(self) -> str:
        return self.model_dump_json()

    @property
    def citation(self) -> dict[str, str]:
        return {
            "title": self.title,
            "source_uri": self.source_uri,
            "chunk_id": self.chunk_id,
        }


@dataclass(frozen=True)
class RetrievedChunk:
    chunk: Chunk
    score: float
    vector_score: float
    lexical_score: float


class ChatRequest(BaseModel):
    user_id: str
    question: str
    top_k: int | None = None


class Citation(BaseModel):
    title: str
    source_uri: str
    chunk_id: str


class SourceReference(BaseModel):
    title: str
    source_uri: str


class ChatResponse(BaseModel):
    request_id: str
    answer: str
    citations: list[Citation]
    retrieved_chunk_ids: list[str]
    retrieved_sources: list[SourceReference] = Field(default_factory=list)
    refusal: bool
    user_id: str
    provider: str
    fallback_used: bool = False
    fallback_reason: str | None = None
    timings_ms: dict[str, float] = Field(default_factory=dict)


class FeedbackRequest(BaseModel):
    request_id: str
    user_id: str
    rating: Literal["up", "down"]
    question: str = ""
    answer: str = ""
    comment: str = ""


class FeedbackResponse(BaseModel):
    status: str
    request_id: str


class EvalResultsResponse(BaseModel):
    status: Literal["ready", "missing"]
    artifact: str
    results: JsonDict | None = None


class FeedbackListResponse(BaseModel):
    status: str
    artifact: str
    count: int
    records: list[JsonDict] = Field(default_factory=list)


class HealthResponse(BaseModel):
    status: str
    vector_backend: str
    collection_count: int | None = None
    index_present: bool
