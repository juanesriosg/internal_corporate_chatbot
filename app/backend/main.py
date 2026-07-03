from __future__ import annotations

from fastapi import FastAPI, HTTPException

from app.backend.config import Settings, get_settings
from app.backend.rag.auth import get_user
from app.backend.rag.embeddings import get_embedding_provider
from app.backend.rag.generator import (
    citations_for,
    get_answer_generator,
    select_context_for_answer,
)
from app.backend.rag.models import ChatRequest, ChatResponse, HealthResponse
from app.backend.rag.retriever import Retriever
from app.backend.rag.storage import load_chunks
from app.backend.rag.vector_store import ChromaVectorStore, index_present

app = FastAPI(title="Internal Corporate Chatbot", version="0.1.0")


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
def chat(request: ChatRequest) -> ChatResponse:
    settings = get_settings()
    try:
        user = get_user(request.user_id)
    except KeyError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    try:
        load_chunks(settings.local_artifact_dir)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    try:
        embedding_provider = get_embedding_provider(settings)
        retriever = Retriever(settings, embedding_provider)
        retrieved = retriever.retrieve(request.question, user, top_k=request.top_k)
        answer_context = select_context_for_answer(request.question, retrieved)
        generator = get_answer_generator(settings)
        answer, refusal = generator.generate(request.question, answer_context)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return ChatResponse(
        answer=answer,
        citations=[] if refusal else citations_for(answer_context),
        retrieved_chunk_ids=[candidate.chunk.chunk_id for candidate in retrieved],
        refusal=refusal,
        user_id=request.user_id,
        provider=settings.llm_provider.value,
    )


def create_app(settings: Settings | None = None) -> FastAPI:
    # Tests can import the module-level app directly; this hook keeps a standard factory available.
    _ = settings
    return app
