# Local Run Playbook

This playbook is for a reviewer or teammate running the chatbot on another
local machine. The intended path is local-first: source documents are in
`mock_data`, generated artifacts go to `.local`, and real secrets stay in
`.env`.

The app code is implemented. The commands below run the local-first prototype.

## Prerequisites

- Python 3.11.
- Git.
- A terminal with access to this repository.
- Optional: an OpenAI API key for the functional LLM path.

No Azure account, AWS account, Docker runtime, or hosted vector database should
be required for the basic local demo.

## 1. Create The Virtual Environment

macOS / Linux / WSL:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Windows PowerShell:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Windows Git Bash:

```bash
py -3.11 -m venv .venv
source .venv/Scripts/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Use Python 3.11 on Windows for this prototype. Python 3.12 and 3.13 can force
Chroma's native `chroma-hnswlib` dependency to compile from source, which
requires Microsoft C++ Build Tools and adds avoidable setup friction.

Do not reuse the same `.venv` between WSL and Windows Git Bash. Create the
environment in the terminal family you will use to run the app.

## 2. Configure Environment Variables

Create a private `.env` from the committed example:

macOS / Linux / WSL:

```bash
cp .env.example .env
```

Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Default provider mode:

```text
LLM_PROVIDER=openai
```

For a no-key smoke-test mode:

```text
LLM_PROVIDER=local
```

For direct OpenAI API mode:

```text
LLM_PROVIDER=openai
OPENAI_API_KEY=<your-local-key>
OPENAI_CHAT_MODEL=<chosen-chat-model>
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
```

For Azure OpenAI mode:

```text
LLM_PROVIDER=azure_openai
AZURE_OPENAI_API_KEY=<your-local-key>
AZURE_OPENAI_ENDPOINT=<your-endpoint>
AZURE_OPENAI_API_VERSION=<api-version>
AZURE_OPENAI_CHAT_DEPLOYMENT=<chat-deployment-name>
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=<embedding-deployment-name>
```

Do not commit `.env`. The repo intentionally tracks only `.env.example`.

## 3. Verify The Mock Corpus

The local corpus should be present:

```bash
python - <<'PY'
import json
from pathlib import Path

manifest = Path("mock_data/manifest.json")
data = json.loads(manifest.read_text())
print(data["corpus_name"])
print(f"documents={len(data['documents'])}")
print(f"sample_questions={len(data['sample_questions'])}")
PY
```

Expected:

```text
Digital Mock Corporate Knowledge Base
documents=20
sample_questions=10
```

## 4. Ingest Documents

Command:

```bash
python -m app.backend.rag.ingest --source mock_data --out .local
```

Expected generated artifacts:

```text
.local/
  chunks.jsonl
  ingest_summary.json
  vector_index/
```

The exact artifact list may grow, but source documents must stay in `mock_data`
and generated files must stay out of Git.

## 5. Run The API

Command:

```bash
uvicorn app.backend.main:app --reload
```

Expected local URLs:

```text
API:      http://127.0.0.1:8000
Swagger:  http://127.0.0.1:8000/docs
Health:   http://127.0.0.1:8000/health
```

## 6. Ask A Question

Request:

```bash
curl -s http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "all_employee",
    "question": "How many PTO days do full-time employees receive?"
  }'
```

Expected response shape:

```json
{
  "answer": "...",
  "citations": [
    {
      "title": "HR PTO Policy 2026",
      "source_uri": "mock_data/pdf/hr/HR_PTO_Policy_2026.pdf",
      "chunk_id": "..."
    }
  ],
  "retrieved_chunk_ids": ["..."],
  "refusal": false
}
```

## 7. Verify Access Control

Engineering user should not retrieve finance or legal restricted documents:

```bash
curl -s http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "eng_user",
    "question": "What are the finance quarter close action items?"
  }'
```

Expected behavior:

- No finance restricted chunks in `retrieved_chunk_ids`.
- Neutral refusal or no authorized information response.
- No disclosure that a restricted finance document exists unless the user is
  authorized.

## 8. Run Evaluation

Command:

```bash
python -m app.backend.rag.eval --source mock_data --index .local
```

Expected output:

- Retrieval recall at 5.
- Citation correctness checks.
- Unauthorized retrieval rate.
- Refusal correctness.
- `.local/eval_results.json`.

## 9. Run Tests

```bash
python -m pytest
```

Expected test coverage:

- Parsing and chunking preserve metadata.
- Retrieval finds expected sources from `mock_data/manifest.json`.
- ACL filters block restricted documents.
- Prompt builder receives only authorized chunks.
- Prompt-injection note is treated as untrusted document content.
- Stale remote-work policy loses to the 2026 policy when the two conflict.

## 10. Useful Maintenance Commands

Rebuild local artifacts:

```bash
rm -rf .local
python -m app.backend.rag.ingest --source mock_data --out .local
```

Lint:

```bash
python -m ruff check app tests
```

Type-check:

```bash
python -m mypy app
```

## Troubleshooting

If dependencies fail to install:

- Confirm Python is 3.11.
- Upgrade pip with `python -m pip install --upgrade pip`.
- Recreate `.venv` from scratch.
- If dependency install is slow on WSL, keep the project under the Linux
  filesystem instead of a Windows-mounted path. Chroma has a larger dependency
  tree and writes many files during installation.

If `.env` is missing:

- Copy `.env.example` again.
- Use `LLM_PROVIDER=local` only if no API key should be required.

If OpenAI requests fail:

- Confirm `OPENAI_API_KEY` is set only in `.env`.
- Confirm `LLM_PROVIDER=openai`.
- Confirm the selected model name is available to the key.

If retrieval returns restricted documents:

- Stop and fix ACL filtering before continuing.
- The invariant is that unauthorized chunks must never reach prompt
  construction.
