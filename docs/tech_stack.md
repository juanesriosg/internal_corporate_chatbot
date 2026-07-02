# Tech Stack Selection

This document explains each layer of the stack, what I would use for the local
prototype, what I would use for a production MVP, and what alternatives I
considered.

The main design choice is to keep the RAG system behind small interfaces:

- `ModelProvider` for generation.
- `EmbeddingProvider` for embeddings.
- `VectorStore` for retrieval.
- `DocumentParser` for parsing source files.

That makes both direct OpenAI API and Azure OpenAI Service viable without
changing chunking, retrieval, access control, or evaluation logic.

## Summary

| Layer | Local Prototype | Production MVP | Alternatives Considered |
| --- | --- | --- | --- |
| LLM provider | Deterministic grounded answer composer first; optional direct OpenAI or Azure OpenAI adapter | Direct OpenAI API or Azure OpenAI Service | Local Llama, Anthropic, Bedrock |
| LLM model | Small/medium OpenAI chat model if API use is enabled | Cost-efficient default model plus stronger escalation model | One large model for every query |
| Embeddings | `text-embedding-3-small` when API use is enabled; deterministic local vectorizer for no-key demo | `text-embedding-3-small`, upgrade to `text-embedding-3-large` if retrieval quality needs it | BGE/e5 local embeddings, Azure AI Search integrated vectorization |
| Vector DB | Chroma persisted under `.local/` | Azure AI Search for hybrid search, or Postgres/pgvector if existing infra prefers it | FAISS, sqlite-vec, Pinecone, Weaviate |
| Orchestration | Custom Python modules | Same custom modules with provider adapters | LangChain, LlamaIndex |
| Parsing | `pypdf`, `python-docx`, `beautifulsoup4`, markdown/plain text parser | Azure AI Document Intelligence or Unstructured for harder files | Custom-only parsing, OCR-only approach |
| Backend API | FastAPI | FastAPI on Azure Container Apps, App Service, or Azure Functions | Flask, Django, Node/NestJS |
| Interface | API docs plus small CLI | Next.js, Microsoft Teams, Slack, or intranet integration | Streamlit-only prototype |
| Metadata | JSON files or SQLite | Azure SQL, Azure Database for PostgreSQL, or Cosmos DB | Store only in vector DB |
| Observability/eval | Structured logs, eval JSON, pytest | Azure Monitor, Application Insights, OpenTelemetry, eval dashboards | Manual testing only |

## LLM Provider And Model

Two provider paths are intentionally supported:

| Option | Why Choose It | When I Would Prefer It |
| --- | --- | --- |
| Direct OpenAI API | Fast setup, clear API surface, clear token pricing, easy local development | Best for this take-home and for a fast MVP when procurement/security allow direct OpenAI |
| Azure OpenAI Service | Fits Azure-first enterprise governance, billing, networking, and identity patterns | Best if the company requires Azure control plane, private networking, or centralized Azure billing |

For the prototype, I would first implement a deterministic grounded answer
composer so the reviewer can run the demo without any API key. Then I would add
a provider adapter that can call either direct OpenAI or Azure OpenAI from
environment variables.

Why not local Llama for the take-home:

- Local model setup is heavier for reviewers.
- Output quality depends on the reviewer's hardware.
- The assignment is about RAG architecture, access control, and engineering
  judgment, not local model hosting.

Why not one large model for every query:

- It makes the cost story worse.
- Most RAG answers should be grounded in retrieved context, so a smaller model
  can answer many questions well.
- Escalation can be reserved for ambiguous, sensitive, or low-confidence cases.

## Embeddings

Prototype choices:

- No-key path: deterministic local vectorizer for smoke tests and ACL
  verification.
- API-enabled path: `text-embedding-3-small`.

Production choices:

- Default: `text-embedding-3-small`.
- Upgrade path: `text-embedding-3-large` if evaluation shows retrieval misses
  that better embeddings fix.

Rationale:

- Embedding cost is usually much smaller than generation cost.
- The smaller embedding model is a pragmatic default.
- The larger model is a measurable quality lever, not a default assumption.

Alternatives considered:

- BGE/e5 local embeddings: good for offline/on-prem variants, but adds local
  model packaging and performance variability.
- Azure AI Search integrated vectorization: useful in Azure production, but
  less transparent for a take-home prototype.

## Vector Database

Prototype:

- Chroma persisted under `.local/`.

Rationale:

- Easy local install.
- Supports metadata storage and vector retrieval.
- Keeps generated index files outside the source corpus.
- Simple enough for a reviewer to inspect and rebuild.

Production:

- Azure AI Search if the company wants managed hybrid search in Azure.
- Postgres/pgvector if the team already operates Postgres and wants simpler
  infrastructure.

Alternatives considered:

- FAISS: fast local vector search, but metadata filtering needs more custom
  code.
- sqlite-vec: attractive local option, but less familiar to many reviewers.
- Pinecone/Weaviate: strong managed vector databases, but not necessary for the
  local prototype and may not match an Azure-first environment.

## Orchestration

Prototype and production:

- Custom orchestration in small Python modules.

Expected modules:

```text
rag/
  ingest.py
  parsers.py
  chunking.py
  embeddings.py
  vector_store.py
  retriever.py
  auth.py
  prompt.py
  generator.py
  eval.py
```

Rationale:

- Access control and prompt construction must be inspectable.
- The assignment evaluates architecture judgment; hiding core decisions inside a
  framework works against that.
- Provider adapters keep OpenAI versus Azure OpenAI replaceable.

Alternatives considered:

- LangChain: useful integrations, but can obscure retrieval and prompt
  boundaries for a small take-home.
- LlamaIndex: strong document/RAG abstractions, but still more framework than
  needed for this prototype.

I would still use framework utilities selectively if they reduce parsing or
evaluation work without becoming the system architecture.

## Document Parsing And Chunking

Prototype parsers:

| Format | Library / Parser |
| --- | --- |
| PDF | `pypdf` |
| DOCX | `python-docx` |
| HTML | `beautifulsoup4` |
| Markdown | Plain text read with heading-aware splitting |
| TXT notes | Plain text read with metadata extraction |

Chunking:

- Split on headings first.
- Fall back to 500 to 900 token chunks.
- Use 100 to 150 token overlap.
- Carry title, source path, department, sensitivity, allowed groups, stale flag,
  and source ACL hash into every chunk.

Alternatives considered:

- Unstructured: stronger broad document parsing, but heavier for a local
  prototype.
- Azure AI Document Intelligence: good production option for scanned or complex
  documents, but unnecessary for local mock documents.
- OCR-first parsing: only needed for scanned PDFs.

## Backend API

Prototype:

- FastAPI.
- `/ingest` for local ingestion trigger or CLI-only ingestion.
- `/chat` for question answering.
- `/eval` for running manifest sample questions.
- FastAPI Swagger UI for interactive review.

Production:

- FastAPI on Azure Container Apps, Azure App Service, or Azure Functions.

Rationale:

- Python is the most direct fit for parsing, embeddings, vector search, and
  RAG evaluation.
- FastAPI gives typed request/response models and automatic API docs.
- The same app can run locally with `uvicorn`.

Alternatives considered:

- Flask: simpler, but weaker typed API ergonomics.
- Django: too heavy for a RAG service.
- Node/NestJS: reasonable for product APIs, less convenient for Python-first
  document and evaluation tooling.

## Frontend / Interface

Prototype:

- API-first through FastAPI Swagger UI.
- Small CLI for repeatable examples and evaluation.

This is intentionally minimal. The assignment needs a working prototype, but
not a full product UI. API docs and a CLI are enough to show ingestion,
retrieval, ACL behavior, citations, refusals, and eval output.

Production:

- Next.js web UI, Microsoft Teams, Slack, or internal intranet integration.

Alternatives considered:

- Streamlit: fast for demos, but less representative of an internal corporate
  chatbot architecture.
- Full Next.js UI in the take-home: visually nicer, but would take time away
  from the RAG and access-control behavior that matters more.

## Observability, Logging, And Evaluation

Prototype:

- Structured JSON logs.
- Eval results written to `.local/eval_results.json`.
- Pytest for chunking, retrieval, and ACL tests.
- Basic latency timings for ingestion, retrieval, and generation.

Production:

- Azure Monitor and Application Insights.
- OpenTelemetry traces.
- LLM-specific eval dashboard or scheduled eval reports.
- Audit log for query ID, user ID hash, retrieved chunk IDs, answer ID, and
  feedback.

Key metrics:

- Retrieval recall at 5.
- Mean reciprocal rank.
- Citation correctness.
- Refusal correctness.
- Unauthorized retrieval rate, target 0.
- End-to-end latency.
- Token usage and cost per request.

Alternatives considered:

- Manual testing only: insufficient because RAG changes can regress silently.
- Vendor-only LLM observability: useful, but not enough for ACL and retrieval
  correctness.
