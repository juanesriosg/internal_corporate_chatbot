from __future__ import annotations

import secrets
import time
import uuid
from datetime import UTC, datetime
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from app.backend.config import LLMProvider, Settings, get_settings
from app.backend.rag.auth import MockUser, get_user
from app.backend.rag.embeddings import get_embedding_provider
from app.backend.rag.generator import (
    LocalAnswerGenerator,
    citations_for,
    get_answer_generator,
    select_context_for_answer,
)
from app.backend.rag.models import (
    ChatRequest,
    ChatResponse,
    Chunk,
    FeedbackRequest,
    FeedbackResponse,
    HealthResponse,
    RetrievedChunk,
)
from app.backend.rag.retriever import Retriever, retrieve_keyword_fallback
from app.backend.rag.storage import append_jsonl, feedback_path, load_chunks
from app.backend.rag.vector_store import ChromaVectorStore, index_present

app = FastAPI(title="Internal Corporate Chatbot", version="0.1.0")
security = HTTPBasic(auto_error=False)

_startup_settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=_startup_settings.cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


def require_api_auth(
    credentials: Annotated[HTTPBasicCredentials | None, Depends(security)],
) -> None:
    settings = get_settings()
    if not settings.api_auth_enabled:
        return

    if not settings.api_basic_username or not settings.api_basic_password:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API authentication is enabled but credentials are not configured.",
        )

    if credentials is None:
        raise _auth_error()

    username_ok = secrets.compare_digest(
        credentials.username.encode("utf-8"),
        settings.api_basic_username.encode("utf-8"),
    )
    password_ok = secrets.compare_digest(
        credentials.password.encode("utf-8"),
        settings.api_basic_password.encode("utf-8"),
    )
    if not username_ok or not password_ok:
        raise _auth_error()


def _auth_error() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required.",
        headers={"WWW-Authenticate": "Basic"},
    )


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    settings = get_settings()
    count: int | None = None
    present = index_present(settings.local_artifact_dir)
    if present:
        try:
            count = ChromaVectorStore.from_settings(settings).count()
        except Exception:
            count = None
    return HealthResponse(
        status="ok",
        vector_backend=settings.vector_backend,
        collection_count=count,
        index_present=present,
    )


@app.post("/chat", response_model=ChatResponse)
def chat(
    request: ChatRequest,
    _auth: Annotated[None, Depends(require_api_auth)],
) -> ChatResponse:
    request_id = uuid.uuid4().hex
    total_start = time.perf_counter()
    timings: dict[str, float] = {}
    settings = get_settings()
    try:
        user = get_user(request.user_id)
    except KeyError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    try:
        chunks = load_chunks(settings.local_artifact_dir)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    retrieved: list[RetrievedChunk]
    answer_context: list[RetrievedChunk]
    answer: str
    refusal: bool
    provider = settings.llm_provider.value
    fallback_used = False
    fallback_reason: str | None = None

    try:
        retrieval_start = time.perf_counter()
        embedding_provider = get_embedding_provider(settings)
        retriever = Retriever(settings, embedding_provider)
        retrieved = retriever.retrieve(request.question, user, top_k=request.top_k)
        timings["retrieval_ms"] = _elapsed_ms(retrieval_start)

        context_start = time.perf_counter()
        answer_context = select_context_for_answer(request.question, retrieved)
        timings["context_ms"] = _elapsed_ms(context_start)

        generation_start = time.perf_counter()
        generator = get_answer_generator(settings)
        answer, refusal = generator.generate(request.question, answer_context)
        timings["generation_ms"] = _elapsed_ms(generation_start)
    except Exception as exc:
        if settings.llm_provider == LLMProvider.LOCAL:
            raise HTTPException(status_code=500, detail="Local chat generation failed.") from exc
        fallback_used = True
        fallback_reason = type(exc).__name__
        provider = f"{settings.llm_provider.value}->local"
        fallback_start = time.perf_counter()
        retrieved, answer_context, answer, refusal = _local_fallback_answer(
            request=request,
            user=user,
            chunks=chunks,
            settings=settings,
        )
        timings["fallback_ms"] = _elapsed_ms(fallback_start)

    timings["total_ms"] = _elapsed_ms(total_start)

    return ChatResponse(
        request_id=request_id,
        answer=answer,
        citations=[] if refusal else citations_for(answer_context),
        retrieved_chunk_ids=[candidate.chunk.chunk_id for candidate in retrieved],
        refusal=refusal,
        user_id=request.user_id,
        provider=provider,
        fallback_used=fallback_used,
        fallback_reason=fallback_reason,
        timings_ms=timings,
    )


@app.post("/feedback", response_model=FeedbackResponse)
def feedback(
    request: FeedbackRequest,
    _auth: Annotated[None, Depends(require_api_auth)],
) -> FeedbackResponse:
    settings = get_settings()
    payload = request.model_dump()
    payload["created_at"] = datetime.now(UTC).isoformat()
    append_jsonl(feedback_path(settings.local_artifact_dir), payload)
    return FeedbackResponse(status="ok", request_id=request.request_id)


def _local_fallback_answer(
    request: ChatRequest,
    user: MockUser,
    chunks: list[Chunk],
    settings: Settings,
) -> tuple[list[RetrievedChunk], list[RetrievedChunk], str, bool]:
    retrieved = retrieve_keyword_fallback(
        question=request.question,
        user=user,
        chunks=chunks,
        top_k=request.top_k or settings.retrieval_top_k,
    )
    answer_context = select_context_for_answer(request.question, retrieved)
    answer, refusal = LocalAnswerGenerator().generate(request.question, answer_context)
    note = (
        "The configured OpenAI provider was unavailable, so I used the local "
        "fallback answer composer for this response.\n\n"
    )
    return retrieved, answer_context, f"{note}{answer}", refusal


def _elapsed_ms(start: float) -> float:
    return round((time.perf_counter() - start) * 1000, 2)


def create_app(settings: Settings | None = None) -> FastAPI:
    # Tests can import the module-level app directly; this hook keeps a standard factory available.
    _ = settings
    return app
