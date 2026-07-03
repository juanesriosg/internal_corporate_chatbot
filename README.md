# Internal Corporate Chatbot Take-Home

This repository is a take-home assignment for designing and prototyping an internal corporate chatbot. The chatbot lets employees ask questions over internal knowledge bases such as HR policies, engineering runbooks, project wikis, and department documentation.

The proposed system is a retrieval-augmented generation (RAG) application. It retrieves relevant internal documents, filters them by the employee's access rights, builds a grounded prompt, and returns an answer with source citations.

## Current Status

The repository contains the architecture, tech stack rationale, cost model, local
mock corpus, and a local-first prototype for ingestion, Chroma retrieval,
access control, grounded answers, and evaluation.

| Area | Status | Location |
| --- | --- | --- |
| Architecture overview | Ready | [docs/architecture.md](docs/architecture.md) |
| Azure/model provider alignment | Ready | [docs/architecture.md](docs/architecture.md#cloud-and-model-provider-alignment) |
| Tech stack rationale | Ready | [docs/tech_stack.md](docs/tech_stack.md) |
| Local run playbook | Ready | [docs/run_playbook.md](docs/run_playbook.md) |
| Local mock corpus | Ready | [mock_data/README.md](mock_data/README.md) and [mock_data/manifest.json](mock_data/manifest.json) |
| Cost estimate | Ready | [docs/costs.md](docs/costs.md) |
| Working prototype | Implemented | `app/`, `tests/`, and `.local/` generated at runtime |
| Architecture diagram | Ready as Mermaid | [docs/architecture.md](docs/architecture.md#end-to-end-flow) |

## Assignment Map

| Assignment Requirement | Where It Is Addressed |
| --- | --- |
| End-to-end data flow | [Architecture: End-To-End Flow](docs/architecture.md#end-to-end-flow) |
| Local prototype constraints | [Architecture: Local Prototype Contract](docs/architecture.md#local-prototype-contract) |
| Ingestion pipeline | [Architecture: Ingestion Pipeline](docs/architecture.md#ingestion-pipeline) |
| Retrieval strategy | [Architecture: Retrieval Strategy](docs/architecture.md#retrieval-strategy) |
| LLM orchestration | [Architecture: LLM Orchestration](docs/architecture.md#llm-orchestration) |
| Authentication and access control | [Architecture: Authorization And Isolation](docs/architecture.md#authorization-and-isolation) |
| Multi-tenancy or department isolation | [Architecture: Authorization And Isolation](docs/architecture.md#authorization-and-isolation) |
| Azure production mapping | [Architecture: Cloud And Model Provider Alignment](docs/architecture.md#cloud-and-model-provider-alignment) |
| Tech stack selection | [docs/tech_stack.md](docs/tech_stack.md) |
| Local run instructions | [docs/run_playbook.md](docs/run_playbook.md) |
| Implementation approach | [Architecture: Prototype Acceptance Criteria](docs/architecture.md#prototype-acceptance-criteria) |
| Evaluation approach | [Architecture: Evaluation Plan](docs/architecture.md#evaluation-plan) |
| Four-week versus three-month plan | [Architecture: Roadmap](docs/architecture.md#roadmap) |
| Cost estimate | [docs/costs.md](docs/costs.md) |

## Proposed System

The system has five core boundaries:

1. Document ingestion parses internal documents, chunks them, attaches metadata and access-control information, and indexes embeddings.
2. Retrieval finds relevant chunks using vector search and, in production, keyword search plus optional re-ranking.
3. Authorization filters documents by tenant, department, group, and role before any chunk reaches the LLM prompt.
4. LLM orchestration builds a grounded prompt, asks the model to answer only from retrieved context, and returns citations.
5. Evaluation and observability measure retrieval quality, refusal behavior, answer groundedness, latency, and cost.

The production version is mapped to Azure-native application services because the target company works primarily in Azure. The architecture keeps cloud-neutral boundaries, while model calls stay behind an adapter that can use either direct OpenAI API or Azure OpenAI Service.

## Local Prototype Contract

The take-home prototype must run locally in the simplest possible way. Cloud services are part of the production architecture, not a requirement for running the demo.

Local-only requirements:

- Use [mock_data](mock_data) as the only ingestion source.
- Read document metadata, ACL rules, stale flags, and sample questions from [mock_data/manifest.json](mock_data/manifest.json).
- Parse local files from `mock_data` across markdown, text notes, HTML, PDF, and DOCX formats.
- Generate chunks locally.
- Generate embeddings with OpenAI by default, or with the local deterministic provider for no-key smoke tests.
- Store the vector index locally in Chroma.
- Run retrieval, ACL filtering, prompt construction, and evaluation locally.
- Avoid requiring Azure, AWS, Docker, or a hosted vector database for the basic demo path.

Suggested generated local artifacts:

```text
.local/
  chunks.jsonl
  ingest_summary.json
  vector_index/
  eval_results.json
```

These files should be reproducible from `mock_data` and should not be treated as source documents.

## Prototype Plan

The prototype should prove the critical RAG loop without requiring production infrastructure.

Implemented local scope:

- The `mock_data` corpus as the source of truth.
- Local ingestion and chunking.
- Direct OpenAI embeddings and chat generation from `.env`.
- Optional local deterministic embeddings and answer generation for no-key smoke tests.
- Mock user identities and group claims.
- Chat API that returns grounded answers with citations.
- Tests for chunking, retrieval, and access control.
- The sample questions and ACL tests defined in `mock_data/manifest.json`.

Implemented repo shape:

```text
app/
  backend/
    config.py
    main.py
    rag/
      auth.py
      embeddings.py
      eval.py
      generator.py
      ingest.py
      chunking.py
      manifest.py
      models.py
      parsers.py
      retriever.py
      storage.py
      vector_store.py
mock_data/
  manifest.json
  markdown/
  notes/
  html/
  pdf/
  word/
tests/
    test_api.py
    test_ingestion.py
    test_retrieval_acl.py
docs/
  architecture.md
  tech_stack.md
  costs.md
```

Local run contract:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
cp .env.example .env
# Edit .env locally and set OpenAI values. Do not commit .env.
python -m app.backend.rag.ingest --source mock_data --out .local
uvicorn app.backend.main:app --reload
```

The repository includes [.env.example](.env.example) so reviewers know which configuration values are needed. Real secrets belong only in `.env`, which is ignored by Git.

See [docs/run_playbook.md](docs/run_playbook.md) for the full local setup and operation playbook.

## Security Posture

The most important design rule is that authorization happens before prompt construction.

The LLM should never receive unauthorized chunks and should never be asked to decide whether the user has access. Access decisions belong to deterministic application code using identity-provider claims and document ACL metadata.

For a user without access to restricted material, the assistant should return a neutral response such as:

```text
I could not find enough authorized information to answer that.
```

It should not reveal that a restricted document exists.

## Known Tradeoffs

- The prototype should optimize for inspectability over production scale.
- A local vector store is enough for the demo, while production may use Azure AI Search for vector and hybrid retrieval.
- A custom orchestration layer is preferred over hiding the core flow inside LangChain or LlamaIndex. Those frameworks can still be useful for loaders or utilities.
- Exact model and embedding choices should remain configurable. The cost model should verify current pricing before final submission.

## Remaining Work

1. Decide whether Swagger/API-only is enough for submission or add a small web
   UI.
2. Run a live OpenAI smoke test with a private `OPENAI_API_KEY`.
3. Add dedicated regression fixtures for ambiguous and out-of-scope questions.
4. Add structured runtime telemetry for latency, token usage, and retrieval
   decisions.
