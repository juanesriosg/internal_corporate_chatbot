---
doc_id: PROJ-ATLAS-009
department: Product
sensitivity: internal
allowed_groups: [product, engineering, design, executives]
tenant_id: northstar
effective_date: 2026-06-25
owner: Product Operations
stale: false
---
# Project Atlas Status Wiki

## Overview

Project Atlas is the internal knowledge assistant pilot for Northstar Digital. The first pilot covers HR policies, platform engineering runbooks, and product launch checklists.

## Milestones

- Week 1: mock document corpus, local ingestion, and basic retrieval.
- Week 2: chat API, citations, and no-answer behavior.
- Week 3: mock SSO claims and ACL filtering.
- Week 4: evaluation dataset, cost model, and pilot demo.

## Success Criteria

The pilot is successful if retrieval Recall@5 is above 80 percent on the golden question set, unauthorized retrieval rate is zero, and at least 70 percent of pilot users rate answers as useful.

## Risks

The largest risks are stale documents, weak access-control propagation, and over-reliance on the LLM when retrieved context is insufficient.
