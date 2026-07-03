# Cost Estimate

This estimate prices the production version of the chatbot, not the local take-home prototype. The prototype is expected to run locally with Chroma under `.local/`; paid model usage is optional during development.

The numeric baseline uses the direct OpenAI API because it is the fastest path for development and local testing. Azure OpenAI Service is also a good production option for an Azure-oriented company. The app should keep both behind the same provider adapter so retrieval, ACL filtering, prompt construction, and evaluation do not change when the provider changes.

Pricing was checked on 2026-07-03 against official sources:

- OpenAI API pricing: <https://developers.openai.com/api/docs/pricing>
- OpenAI embeddings guide: <https://developers.openai.com/api/docs/guides/embeddings>
- OpenAI embedding model announcement and pricing details: <https://openai.com/index/new-embedding-models-and-api-updates/>
- Azure OpenAI pricing overview: <https://azure.microsoft.com/en-us/pricing/details/azure-openai/>
- Azure Retail Prices API: <https://learn.microsoft.com/en-us/rest/api/cost-management/retail-prices/azure-retail-prices>
- Azure AI Search pricing: <https://azure.microsoft.com/en-us/pricing/details/search/>
- Azure AI Search tier guidance: <https://learn.microsoft.com/en-us/azure/search/search-sku-tier>
- Azure AI Search vector search overview: <https://learn.microsoft.com/en-us/azure/search/vector-search-overview>
- Azure OpenAI quota guidance: <https://learn.microsoft.com/en-us/azure/foundry/openai/quotas-limits>

Azure prices below are public retail prices queried from the Azure Retail Prices API for `eastus` in USD. Actual Azure pricing can change by region, deployment type, currency, enterprise agreement, reservation, and private discount.

## Scope

Included:

- Chat generation with OpenAI or Azure OpenAI.
- Query embeddings and corpus indexing embeddings.
- Local/self-hosted vector retrieval as the primary design.
- Optional OpenAI File Search or Azure AI Search as managed retrieval alternatives.
- Runtime hosting, storage, observability, evaluation, and one-time build estimates.
- Cost levers and scale scenarios.

Not included:

- ChatGPT Business or Enterprise seats.
- Enterprise support contracts.
- Procurement, legal, or compliance certification costs.
- Large-scale data migration outside the chatbot corpus.
- AWS Bedrock pricing.

## Baseline Assumptions

| Assumption | Value |
| --- | ---: |
| Company size | 500 to 2,000 employees |
| Monthly active chatbot users | 1,000 |
| Queries per active user per month | 25 |
| Monthly queries | 25,000 |
| Average generation input per query | 3,500 tokens |
| Average generation output per query | 600 tokens |
| Average query embedding input | 100 tokens |

Monthly token volume:

| Token Type | Formula | Monthly Tokens |
| --- | --- | ---: |
| Generation input | 25,000 queries x 3,500 tokens | 87.5M |
| Generation output | 25,000 queries x 600 tokens | 15.0M |
| Query embeddings | 25,000 queries x 100 tokens | 2.5M |

The base model is `gpt-5.4-mini`, with `gpt-5.4` as the escalation model for sensitive, ambiguous, or low-confidence answers.

## Model Provider Pricing

Direct OpenAI API standard token prices:

| Model | Input / 1M | Cached Input / 1M | Output / 1M | Use |
| --- | ---: | ---: | ---: | --- |
| `gpt-5.4-mini` | $0.75 | $0.075 | $4.50 | Base answer model |
| `gpt-5.4` | $2.50 | $0.25 | $15.00 | Escalation model |
| `gpt-5.5` | $5.00 | $0.50 | $30.00 | Premium sensitivity check |

Azure OpenAI Service equivalent public retail prices, queried from the Azure Retail Prices API for East US Global meters:

| Azure Meter | Input / 1M | Cached Input / 1M | Output / 1M | Notes |
| --- | ---: | ---: | ---: | --- |
| GPT-5.4 mini Global | $0.75 | $0.075 | $4.50 | Matches direct OpenAI baseline in this region/meter |
| GPT-5.4 Global | $2.50 | $0.25 | $15.00 | Matches direct OpenAI baseline in this region/meter |
| GPT-5.5 short context Global | $5.00 | $0.50 | $30.00 | Matches direct OpenAI baseline in this region/meter |

Azure Data Zone and priority processing meters are higher. For example, the Retail Prices API returned GPT-5.4 mini Data Zone at $0.825 input, $0.0825 cached input, and $4.95 output per 1M tokens, and priority processing at $1.50 input, $0.15 cached input, and $9.00 output per 1M tokens.

OpenAI and Azure both have Batch API style discounts for offline work. Use batch processing for large asynchronous indexing, eval, or summarization jobs when a 24-hour turnaround is acceptable.

## Monthly Generation Cost

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

Base embedding model: `text-embedding-3-small`.

Upgrade option: `text-embedding-3-large` only if retrieval evals prove the smaller model is not good enough.

OpenAI embedding prices:

| Embedding Model | Price / 1M Tokens | Dimensions | Use |
| --- | ---: | ---: | --- |
| `text-embedding-3-small` | $0.02 | 1,536 | Base RAG embedding model |
| `text-embedding-3-large` | $0.13 | 3,072 | Quality upgrade |

Azure Retail Prices API returned the same East US Global embedding rates for `text-embedding-3-small` and `text-embedding-3-large`. Regional/Data Zone Azure embedding meters were about 10% higher in the queried rows.

Monthly query embedding cost:

```text
2.5M monthly query embedding tokens x $0.02 / 1M = $0.05 / month
```

Initial corpus indexing cost:

| Corpus Size | Tokens To Embed | `text-embedding-3-small` | `text-embedding-3-large` |
| --- | ---: | ---: | ---: |
| Small pilot | 10M | $0.20 one-time | $1.30 one-time |
| Realistic MVP | 100M | $2.00 one-time | $13.00 one-time |
| Larger rollout | 500M | $10.00 one-time | $65.00 one-time |

Embedding API cost is not the main cost driver. Generation output tokens, context size, model tier, and managed infrastructure dominate the monthly bill.

## Retrieval And Vector Storage Cost

Recommended path:

- Prototype: local Chroma under `.local/`, $0 hosted cost.
- MVP: app-owned Chroma, SQLite, or Postgres/pgvector if the company already operates a database.
- Azure production option: Azure AI Search when the company wants managed vector and hybrid search, operational scaling, and Azure-native governance.

Azure AI Search supports vector search over embeddings and has billable Basic and Standard tiers. Microsoft guidance describes Basic as production-capable up to three replicas, with Standard tiers as the default for scaling partitions and replicas.

Azure AI Search East US retail rates queried from the Azure Retail Prices API:

| Azure AI Search Meter | Retail Price | Monthly Estimate |
| --- | ---: | ---: |
| Basic Unit | $0.101/hour | ~$74/month |
| Standard S1 Unit | $0.336/hour | ~$245/month |
| Standard S2 Unit | $1.344/hour | ~$981/month |
| Standard S3 Unit | $2.688/hour | ~$1,962/month |
| Semantic Ranker Unit | $16.12/day | ~$484/month |
| Semantic Ranker Overage | $2.00/1K queries | Usage-based |

For the take-home and first MVP, I would keep retrieval app-owned unless managed Azure AI Search is explicitly required. App-owned retrieval makes ACL behavior easier to inspect and test. Azure AI Search becomes more attractive when hybrid search, indexers, replicas, and operational ownership matter more than cost.

## Optional OpenAI File Search

The current implementation does not use OpenAI File Search. It owns retrieval locally so ACL filtering can happen before context is sent to the LLM.

OpenAI File Search is a managed alternative. The official pricing page lists:

- Storage: $0.10 per GB per day after 1 GB free.
- Tool calls: $2.50 per 1,000 calls.

If every chatbot request used one File Search call:

```text
25,000 monthly calls / 1,000 x $2.50 = $62.50 / month
```

Storage example:

```text
10 GB stored - 1 GB free = 9 billable GB
9 GB x $0.10 / GB-day x 30 days = $27.00 / month
```

Optional File Search subtotal:

```text
$62.50 tool calls + $27.00 storage = $89.50 / month
```

This is not expensive at the baseline volume, but it moves retrieval and parts of the index lifecycle into OpenAI's managed layer. For sensitive internal documents, the ACL and deletion behavior would need extra design review.

## Hosting, Observability, And Eval Cost

Local prototype:

| Component | Monthly Cost |
| --- | ---: |
| FastAPI app on local machine | $0 |
| Chroma local index | $0 |
| Local eval run | $0 plus optional model tokens |

Production Azure-oriented MVP:

| Component | Monthly Estimate | Notes |
| --- | ---: | --- |
| Azure Container Apps API and ingestion worker | $75 to $250 | One or two small always-on equivalents; scale-to-zero can reduce dev cost |
| Azure Key Vault, storage, networking | $25 to $100 | Secrets, artifacts, logs, private networking depending on policy |
| Azure AI Search Basic or S1, if managed retrieval is used | $75 to $250 | Basic to S1 range for early MVP |
| Azure AI Search semantic ranker, optional | $0 to $500+ | Add only if quality evals justify it |
| Azure Monitor / Application Insights | $50 to $300 | Depends mostly on retained logs and traces |
| Scheduled eval jobs | $25 to $150 | Golden set, ACL tests, regression reports |

Self-hosted retrieval MVP:

| Component | Monthly Estimate | Notes |
| --- | ---: | --- |
| Runtime hosting | $75 to $250 | API plus background ingestion worker |
| Vector/database storage | $0 to $100 | Reuse existing database or local disk for pilot |
| Observability and eval | $75 to $450 | Logs, traces, dashboards, scheduled eval |

## Monthly MVP Summary

Base MVP with app-owned retrieval and `gpt-5.4-mini`:

| Component | Monthly Estimate |
| --- | ---: |
| Generation | ~$135 |
| Query embeddings | <$1 |
| Corpus re-embedding | $0 to $20 |
| Runtime, storage, observability, eval | $150 to $800 |
| Total | ~$300 to $1,000/month |

Base MVP with Azure AI Search Basic/S1:

| Component | Monthly Estimate |
| --- | ---: |
| Generation | ~$135 |
| Query embeddings | <$1 |
| Corpus re-embedding | $0 to $20 |
| Runtime, storage, observability, eval | $150 to $800 |
| Azure AI Search Basic/S1 | ~$75 to $250 |
| Total | ~$375 to $1,250/month |

Mixed routing with 80% `gpt-5.4-mini` and 20% `gpt-5.4`:

| Component | Monthly Estimate |
| --- | ---: |
| Generation | ~$195 |
| Other operating costs, app-owned retrieval | $150 to $800 |
| Other operating costs, Azure AI Search Basic/S1 | $225 to $1,050 |
| Total with app-owned retrieval | ~$350 to $1,000/month |
| Total with Azure AI Search | ~$425 to $1,250/month |

All queries on `gpt-5.4`:

| Component | Monthly Estimate |
| --- | ---: |
| Generation | ~$445 |
| Other operating costs | $150 to $1,050 |
| Total | ~$600 to $1,500/month |

Premium all-`gpt-5.5` sensitivity case:

| Component | Monthly Estimate |
| --- | ---: |
| Generation | ~$890 |
| Other operating costs | $150 to $1,050 |
| Total | ~$1,050 to $1,950/month |

## Scaling To 100,000 Monthly Queries

At 100,000 monthly queries, token volume is 4x the baseline.

| Scenario | Generation Cost |
| --- | ---: |
| All `gpt-5.4-mini` | ~$533/month |
| 80% `gpt-5.4-mini`, 20% `gpt-5.4` | ~$781/month |
| All `gpt-5.4` | ~$1,775/month |
| All `gpt-5.5` | ~$3,550/month |

Infrastructure may also need to scale at this point. If Azure AI Search is used, the larger cost risk is usually moving from Basic/S1 to more replicas, more partitions, semantic ranker, or S2/S3 tiers.

## One-Time Real MVP Build Cost

This is not a take-home prototype labor estimate. It is the expected implementation investment for a real company MVP that supports one or two departments with production identity, monitored ingestion, RAG quality tests, and access-control guarantees.

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

A narrower pilot with fewer connectors and no chat-platform integration could land closer to $35k to $60k. A production rollout across many departments, strict compliance, and multiple enterprise connectors can exceed $150k before ongoing support.

## One-Time Non-Labor Setup Costs

These are setup costs separate from engineering hours. Many may be $0 if the company already has Azure resources, monitoring, CI/CD, and security tooling.

| Setup Item | Estimate | Notes |
| --- | ---: | --- |
| Initial corpus parsing and embedding | $5 to $100 | Model cost is low; setup and validation matter more |
| Initial vector index storage | $0 to $300 | $0 for local/self-hosted pilot; higher for managed search |
| Runtime environment setup | $0 to $500 | App/container resources, secrets, service principals, networking |
| Observability setup | $0 to $300 | Dashboards, log retention, traces, alerts |
| Security review tooling | $0 to $1,000 | Depends on existing SAST, DAST, secret scanning, and policy tooling |
| Evaluation dataset setup | $0 to $250 | Small hosted eval jobs or storage; mostly labor-driven |
| Total setup range | ~$0 to $2,500 | Excludes engineering labor |

For the take-home prototype, these setup costs should be effectively $0 because generated artifacts live under `.local/`.

## Cost Levers

Most important levers:

- Model tiering: route simple questions to `gpt-5.4-mini`; reserve larger models for ambiguous, policy-sensitive, or low-confidence answers.
- Context budget: cap chunks and tokens per answer. Retrieval quality is cheaper than sending excessive context.
- Output budget: concise answers with citations reduce output-token cost.
- Prompt caching: keep stable system and policy instructions cache-friendly where the provider supports it.
- Answer caching: cache only when safe, keyed by tenant, user group set, document ACL hash, and source version.
- Incremental indexing: re-embed changed documents only, not the full corpus.
- Batch processing: use Batch APIs for offline re-indexing, eval, or summarization jobs.
- Managed retrieval choice: Azure AI Search and OpenAI File Search reduce operational work but add direct monthly cost and require careful ACL/deletion validation.
- Logging volume: redact sensitive content and sample traces so observability does not become a hidden data and cost risk.

## Recommended Position For This Submission

- Prototype: local-first, Chroma-backed, with OpenAI enabled through `.env` but no key committed.
- Primary development provider: direct OpenAI API.
- Production-compatible provider: Azure OpenAI Service for Azure-first governance, private networking, billing, and quota management.
- Base production model: `gpt-5.4-mini`.
- Escalation model: `gpt-5.4`.
- Embeddings: `text-embedding-3-small`, with `text-embedding-3-large` only if evals require it.
- Retrieval: app-owned vector index for the prototype and first MVP; Azure AI Search as the managed Azure production option.
- Expected monthly MVP run rate: roughly $300 to $1,250, depending mainly on managed search, observability, and model routing.
- Expected one-time real MVP build investment: roughly $50k to $130k.
