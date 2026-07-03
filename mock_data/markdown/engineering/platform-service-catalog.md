---
doc_id: ENG-CAT-001
department: Engineering
sensitivity: internal
allowed_groups: [engineering, platform, sre]
tenant_id: default
effective_date: 2026-03-01
owner: Platform Engineering
stale: false
---
# Platform Service Catalog

## Services

### Identity Service
Owns employee and customer authentication. The service emits login audit events, token issuance events, and failed authentication counters.

### Billing Service
Owns customer invoices, subscription state, and payment-provider webhooks. Production access is restricted to the billing squad and on-call SRE.

### Knowledge Assistant Service
Owns the internal RAG chatbot prototype. It depends on the document ingestion worker, vector index, chat API, and evaluation harness.

## Ownership

Every service must have a primary owner, secondary owner, runbook URL, dashboard URL, and escalation channel.

## Operational Requirements

All platform services must publish p95 latency, error rate, saturation, dependency failure count, and deployment version. Services with customer impact must have rollback instructions.
