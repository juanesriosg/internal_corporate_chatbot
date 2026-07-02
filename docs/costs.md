# Cost Estimate

This estimate uses the direct OpenAI API as the priced baseline. Azure OpenAI
Service is also a valid production provider option because the target company is
Azure-oriented, but its final pricing should be checked in the target Azure
subscription and region before committing to a budget.

Pricing was checked on 2026-07-02 against the official OpenAI API pricing and
embeddings documentation:

- OpenAI API pricing: <https://platform.openai.com/docs/pricing>
- OpenAI embeddings guide: <https://platform.openai.com/docs/guides/embeddings>

The take-home prototype should run locally. Its demo path should not require a
paid hosted vector database, cloud infrastructure, or OpenAI API key if the
prototype uses a deterministic local answer composer. This document estimates
the production version where OpenAI models are used for generation and, likely,
embeddings, either through direct OpenAI API or Azure OpenAI Service.

## What Is Included

Included:

- Direct OpenAI API usage for answer generation.
- Direct OpenAI API usage for embeddings.
- Provider decision notes for direct OpenAI API versus Azure OpenAI Service.
- Optional OpenAI File Search cost if we decide to use it instead of a local or
  self-hosted vector index.
- Basic runtime, storage, and observability estimates for a real company MVP.
- One-time real MVP build cost.
- Cost levers and scaling scenarios.

Not included:

- A labor estimate for the take-home prototype.
- AWS Bedrock pricing.
- Azure OpenAI pricing as a final quote. It remains a valid provider option, but
  this estimate does not assume Azure regional pricing or enterprise discounts.
- Enterprise contract discounts.
- Customer support, legal review, procurement, or security certification costs.

## Baseline Assumptions

Company profile:

| Assumption | Value |
| --- | ---: |
| Company size | 500 to 2,000 employees |
| Monthly active chatbot users | 1,000 |
| Queries per active user per month | 25 |
| Monthly queries | 25,000 |

Token assumptions per query:

| Token Type | Estimate | Notes |
| --- | ---: | --- |
| Input tokens | 3,500 | User question, system/developer instructions, retrieved chunks, citation metadata, short conversation context |
| Output tokens | 600 | Grounded answer plus citations |
| Query embedding input | 100 | Short user query or rewritten query |

Monthly token volume:

| Token Type | Formula | Monthly Tokens |
| --- | --- | ---: |
| Generation input | 25,000 queries x 3,500 input tokens | 87.5M |
| Generation output | 25,000 queries x 600 output tokens | 15.0M |
| Query embeddings | 25,000 queries x 100 tokens | 2.5M |

The base model choice is `gpt-5.4-mini`, because it is materially cheaper than
larger models while still being appropriate for a RAG assistant where the
system supplies retrieved context. For complex or sensitive answers, a router
can escalate to `gpt-5.4`.

## Provider Options

Both model-provider paths are acceptable:

| Provider Path | Cost Treatment | When To Prefer |
| --- | --- | --- |
| Direct OpenAI API | Used as the numeric baseline in this document | Fastest iteration, clear direct API pricing, easy local development |
| Azure OpenAI Service | Validate with Azure pricing in the target subscription and region | Azure-first governance, billing, private networking, and enterprise controls |

The implementation should use a provider adapter so switching between these two
paths does not change retrieval, ACL filtering, prompt construction, or
evaluation.

## Current OpenAI Unit Prices Used

OpenAI prices are per 1M tokens on the official pricing page.

| Model | Input | Cached Input | Output | Use In This Estimate |
| --- | ---: | ---: | ---: | --- |
| `gpt-5.4-mini` | $0.75 | $0.075 | $4.50 | Base model |
| `gpt-5.4` | $2.50 | $0.25 | $15.00 | Escalation model |
| `gpt-5.5` | $5.00 | $0.50 | $30.00 | Premium/latest-model sensitivity check |

For embeddings, the OpenAI embeddings guide states that
`text-embedding-3-small` supports roughly 62,500 pages per dollar assuming
about 800 tokens per page. That implies:

```text
62,500 pages x 800 tokens/page = 50,000,000 tokens per $1
$1 / 50M tokens = $0.02 per 1M tokens
```

`text-embedding-3-large` supports roughly 9,615 pages per dollar under the same
800-token page assumption:

```text
9,615 pages x 800 tokens/page = 7,692,000 tokens per $1
$1 / 7.692M tokens ~= $0.13 per 1M tokens
```

The estimate uses `text-embedding-3-small` for the base case and keeps
`text-embedding-3-large` as a quality upgrade if retrieval quality needs it.

## Monthly OpenAI Generation Cost

Base case using `gpt-5.4-mini` for all answers:

```text
Input:  87.5M tokens x $0.75 / 1M = $65.63
Output: 15.0M tokens x $4.50 / 1M = $67.50
Total generation cost = $133.13 / month
```

Mixed routing case with 80% `gpt-5.4-mini` and 20% `gpt-5.4`:

```text
Mini portion:
  Input:  70.0M tokens x $0.75 / 1M = $52.50
  Output: 12.0M tokens x $4.50 / 1M = $54.00
  Mini subtotal = $106.50

Escalated portion:
  Input:  17.5M tokens x $2.50 / 1M = $43.75
  Output:  3.0M tokens x $15.00 / 1M = $45.00
  Escalated subtotal = $88.75

Total generation cost = $195.25 / month
```

All queries on `gpt-5.4`:

```text
Input:  87.5M tokens x $2.50 / 1M = $218.75
Output: 15.0M tokens x $15.00 / 1M = $225.00
Total generation cost = $443.75 / month
```

Premium sensitivity check using `gpt-5.5` for all answers:

```text
Input:  87.5M tokens x $5.00 / 1M = $437.50
Output: 15.0M tokens x $30.00 / 1M = $450.00
Total generation cost = $887.50 / month
```

## Embedding Cost

Query embeddings are tiny compared with generation:

```text
2.5M monthly query embedding tokens x $0.02 / 1M = $0.05 / month
```

Indexing cost depends on corpus size. The `mock_data` corpus is tiny, but a
real company corpus could be much larger.

| Corpus Size | Tokens To Embed | `text-embedding-3-small` | `text-embedding-3-large` |
| --- | ---: | ---: | ---: |
| Small pilot | 10M | $0.20 one-time | $1.30 one-time |
| Realistic MVP | 100M | $2.00 one-time | $13.00 one-time |
| Larger rollout | 500M | $10.00 one-time | $65.00 one-time |

Embeddings are not the main cost driver. Generation output tokens, context
size, and model choice matter more.

## Vector Index Cost

Base architecture:

- Prototype: local vector index under `.local/`, $0 incremental hosting cost.
- MVP: self-hosted local index, SQLite, or Postgres/pgvector if the company
  already has an application database.
- Production: either keep a self-managed vector store or move to a managed
  search/vector service later.

Base estimate assumes no OpenAI File Search charges because retrieval is owned
by the app.

Optional OpenAI File Search estimate:

OpenAI pricing lists File Search storage at $0.10 per GB per day after 1 GB
free, and tool calls at $2.50 per 1,000 calls. If every chatbot request used one
File Search tool call:

```text
25,000 monthly calls / 1,000 x $2.50 = $62.50 / month
```

Storage example:

```text
10 GB stored - 1 GB free = 9 billable GB
9 GB x $0.10 / GB-day x 30 days = $27.00 / month
```

OpenAI File Search optional subtotal for this example:

```text
$62.50 tool calls + $27.00 storage = $89.50 / month
```

I would not use OpenAI File Search for the take-home prototype because local
retrieval makes ACL enforcement easier to inspect. It remains a production
option if the team prefers managed retrieval inside OpenAI's platform.

## Monthly MVP Cost Summary

Base MVP using local/self-hosted retrieval and `gpt-5.4-mini`:

| Component | Monthly Estimate | Notes |
| --- | ---: | --- |
| OpenAI generation | $135 | 25k queries, `gpt-5.4-mini`, rounded |
| OpenAI query embeddings | <$1 | Query embeddings are negligible |
| Corpus re-embedding | $0 to $20 | Usually event-driven; depends on document churn |
| Runtime hosting | $100 to $500 | Small API service and background ingestion worker |
| Database/vector storage | $0 to $300 | $0 if local/self-hosted on existing infra; higher if managed |
| Observability/logging | $50 to $300 | Structured logs, traces, eval reports |
| Scheduled evaluation jobs | $25 to $150 | Golden set, regression tests, safety checks |
| Total base MVP | ~$300 to $1,400/month | Excludes enterprise support and discounts |

Mixed routing MVP:

| Component | Monthly Estimate |
| --- | ---: |
| OpenAI generation with 80% mini / 20% standard | ~$195 |
| Other operating costs | ~$175 to $1,250 |
| Total mixed-routing MVP | ~$400 to $1,500/month |

Higher-quality all-`gpt-5.4` MVP:

| Component | Monthly Estimate |
| --- | ---: |
| OpenAI generation | ~$445 |
| Other operating costs | ~$175 to $1,250 |
| Total higher-quality MVP | ~$650 to $1,700/month |

Premium all-`gpt-5.5` sensitivity case:

| Component | Monthly Estimate |
| --- | ---: |
| OpenAI generation | ~$890 |
| Other operating costs | ~$175 to $1,250 |
| Total premium MVP | ~$1,100 to $2,200/month |

## Scaling To 100,000 Monthly Queries

At 100,000 monthly queries, token volume is 4x the baseline:

| Scenario | Generation Cost |
| --- | ---: |
| All `gpt-5.4-mini` | ~$533/month |
| 80% `gpt-5.4-mini`, 20% `gpt-5.4` | ~$781/month |
| All `gpt-5.4` | ~$1,775/month |
| All `gpt-5.5` | ~$3,550/month |

At this scale, OpenAI model selection and output length become the dominant
cost levers.

## One-Time Real MVP Build Cost

This is not a take-home prototype labor estimate. It is the expected
implementation investment for a real company MVP that supports one or two
departments with production identity, monitored ingestion, RAG quality tests,
and access-control guarantees.

| Workstream | Estimate |
| --- | ---: |
| Backend/RAG implementation | 160 to 240 engineering hours |
| Ingestion and document parsing | 80 to 140 engineering hours |
| Access control and SSO integration | 60 to 100 engineering hours |
| Minimal UI or Teams/Slack integration | 60 to 100 engineering hours |
| Evaluation harness and golden dataset | 50 to 90 engineering hours |
| Observability, deployment, and runbooks | 60 to 100 engineering hours |
| Security review and prompt-injection testing | 40 to 80 engineering hours |
| Total | 510 to 850 hours |

Using a blended internal rate of $100 to $150/hour:

```text
Low:  510 hours x $100/hour = $51,000
High: 850 hours x $150/hour = $127,500
```

Real MVP build estimate:

```text
$50k to $130k one-time
```

A narrower pilot with fewer connectors and no chat-platform integration could
land closer to $35k to $60k. A production rollout across many departments,
strict compliance, and multiple enterprise connectors can exceed $150k before
ongoing support.

## One-Time Non-Labor Setup Costs

These are setup costs separate from engineering hours. Many may be $0 if the
company already has the relevant Azure resources, monitoring, and CI/CD
infrastructure.

| Setup Item | Estimate | Notes |
| --- | ---: | --- |
| Initial corpus parsing and embedding | $5 to $100 | OpenAI embedding cost is low; cost mostly depends on corpus size and reprocessing |
| Initial vector index storage | $0 to $300 | $0 for local/self-hosted pilot; higher for managed search/vector services |
| Runtime environment setup | $0 to $500 | Azure app/container resources, secrets, service principals, networking |
| Observability setup | $0 to $300 | Dashboards, log retention, traces, alerts |
| Security review tooling | $0 to $1,000 | Depends on existing SAST/DAST/secret scanning and policy tooling |
| Evaluation dataset setup | $0 to $250 | Small hosted eval jobs or storage; mostly labor-driven |
| Total setup range | ~$0 to $2,500 | Excludes engineering labor |

For the take-home prototype, these setup costs should be effectively $0 because
the app is local-first and generated artifacts live under `.local/`.

## Cost Levers

Most important levers:

- Model tiering: route simple questions to `gpt-5.4-mini`; reserve larger models
  for ambiguous, policy-sensitive, or low-confidence questions.
- Context budget: cap chunks and tokens per answer. Retrieval quality is cheaper
  than sending excessive context.
- Output budget: concise answers with citations reduce output-token cost.
- Prompt caching: cache stable system and policy instructions where possible.
- Answer caching: cache only when safe, keyed by tenant, user group set,
  document ACL hash, and source version.
- Document churn: re-embed changed documents only, not the entire corpus.
- Eval sampling: run full evals on release and sampled evals on schedule.
- Retrieval ownership: local/self-hosted retrieval avoids per-call managed file
  search charges and keeps ACL behavior inspectable.

## Recommended Cost Position For This Take-Home

Use this position in the submission:

- Prototype: fully local; no paid OpenAI usage required for the basic demo.
- MVP provider: direct OpenAI API or Azure OpenAI Service behind the same
  provider adapter.
- Numeric baseline: direct OpenAI API pricing.
- Base production model: `gpt-5.4-mini`.
- Escalation model: `gpt-5.4` for complex, sensitive, or low-confidence cases.
- Retrieval: local or self-hosted vector index first, not OpenAI File Search.
- Expected monthly MVP run rate: roughly $300 to $1,500.
- Expected one-time real MVP build investment: roughly $50k to $130k.

This keeps the estimate realistic while preserving both viable provider paths:
direct OpenAI for speed and transparent pricing, or Azure OpenAI for Azure-first
enterprise governance.
